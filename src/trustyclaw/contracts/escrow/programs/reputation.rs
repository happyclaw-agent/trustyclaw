//! TrustyClaw On-Chain Reputation Program
//!
//! Stores reputation scores and reviews in Solana PDA accounts.
//! - Reputation PDA: [REPUTATION_SEED, agent_address]
//! - Review PDA: [REVIEW_SEED, review_id]
//! - Review List PDA: [REVIEW_LIST_SEED, agent_address]

use anchor_lang::prelude::*;
use anchor_lang::system_program::{create_account, CreateAccountParams};
use anchor_spl::token::{self, Token, TokenAccount, Transfer};
use std::mem::size_of;

declare_id!("REPUT1111111111111111111111111111111111111");

const REPUTATION_SEED: &[u8] = b"trustyclaw-reputation";
const REVIEW_SEED: &[u8] = b"trustyclaw-review";
const REVIEW_LIST_SEED: &[u8] = b"trustyclaw-reviews";

const MAX_REVIEWS_PER_AGENT: u32 = 1000;
const REVIEW_ID_LENGTH: usize = 32;
const COMMENT_LENGTH: usize = 256;

#[program]
pub mod reputation {
    use super::*;

    /// Initialize a reputation account for an agent
    ///
    /// Accounts:
    /// - payer: Account paying for account creation
    /// - reputation_account: PDA to hold reputation state
    /// - system_program: For account creation
    #[access_control(not_initialized(&ctx))]
    pub fn initialize_reputation(ctx: Context<InitializeReputation>) -> Result<()> {
        let reputation = &mut ctx.accounts.reputation_account;
        
        reputation.agent = ctx.accounts.agent.key();
        reputation.total_reviews = 0;
        reputation.average_rating = 0;
        reputation.on_time_percentage = 100;
        reputation.reputation_score = 50; // Starting score
        reputation.positive_votes = 0;
        reputation.negative_votes = 0;
        reputation.review_count = 0;
        reputation.created_at = Clock::get()?.unix_timestamp;
        reputation.updated_at = Clock::get()?.unix_timestamp;
        
        emit!(ReputationInitialized {
            agent: ctx.accounts.agent.key(),
            reputation_score: reputation.reputation_score,
        });
        
        Ok(())
    }

    /// Submit a review for an agent
    ///
    /// Accounts:
    /// - reviewer: Account submitting the review
    /// - reputation_account: Target agent's reputation
    /// - review_account: PDA to hold the review
    /// - system_program: For account creation
    #[access_control(reputation_exists(&ctx))]
    pub fn submit_review(
        ctx: Context<SubmitReview>,
        review_id: [u8; 32],
        rating: u8,
        completed_on_time: bool,
        comment_hash: [u8; 32],
    ) -> Result<()> {
        require!(rating >= 1 && rating <= 5, ReviewError::InvalidRating);
        
        let review = &mut ctx.accounts.review_account;
        let reputation = &mut ctx.accounts.reputation_account;
        
        // Initialize review
        review.review_id = review_id;
        review.provider = ctx.accounts.provider.key();
        review.reviewer = ctx.accounts.reviewer.key();
        review.rating = rating;
        review.completed_on_time = completed_on_time;
        review.comment_hash = comment_hash;
        review.positive_votes = 0;
        review.negative_votes = 0;
        review.timestamp = Clock::get()?.unix_timestamp;
        
        // Update reputation
        let new_total = (reputation.total_reviews as f64 * reputation.average_rating) + (rating as f64);
        reputation.total_reviews = reputation.total_reviews.checked_add(1).unwrap();
        reputation.average_rating = new_total / (reputation.total_reviews as f64);
        
        if completed_on_time {
            reputation.on_time_percentage = ((reputation.on_time_percentage as f64 * 
                (reputation.total_reviews as f64 - 1.0)) + 100.0) / (reputation.total_reviews as f64);
        }
        
        // Recalculate reputation score
        reputation.reputation_score = calculate_score(
            reputation.average_rating,
            reputation.on_time_percentage,
            reputation.total_reviews as u32,
        );
        
        reputation.updated_at = Clock::get()?.unix_timestamp;
        
        emit!(ReviewSubmitted {
            review_id,
            provider: ctx.accounts.provider.key(),
            reviewer: ctx.accounts.reviewer.key(),
            rating,
        });
        
        Ok(())
    }

    /// Update reputation score based on all reviews
    ///
    /// Accounts:
    /// - authority: Account calling the update
    /// - reputation_account: Agent's reputation to update
    #[access_control(reputation_exists(&ctx))]
    pub fn update_score(ctx: Context<UpdateScore>) -> Result<()> {
        let reputation = &mut ctx.accounts.reputation_account;
        
        // Recalculate score from current metrics
        reputation.reputation_score = calculate_score(
            reputation.average_rating,
            reputation.on_time_percentage,
            reputation.total_reviews as u32,
        );
        
        reputation.updated_at = Clock::get()?.unix_timestamp;
        
        emit!(ScoreUpdated {
            agent: reputation.agent,
            new_score: reputation.reputation_score,
        });
        
        Ok(())
    }

    /// Vote on a review (upvote or downvote)
    ///
    /// Accounts:
    /// - voter: Account casting the vote
    /// - review_account: Review being voted on
    #[access_control(review_exists(&ctx))]
    pub fn vote_review(
        ctx: Context<VoteReview>,
        review_id: [u8; 32],
        vote_up: bool,
    ) -> Result<()> {
        let review = &mut ctx.accounts.review_account;
        
        if vote_up {
            review.positive_votes = review.positive_votes.checked_add(1).unwrap();
        } else {
            review.negative_votes = review.negative_votes.checked_add(1).unwrap();
        }
        
        emit!(ReviewVoted {
            review_id,
            voter: ctx.accounts.voter.key(),
            vote_up,
        });
        
        Ok(())
    }

    /// Get current reputation score for an agent
    ///
    /// Accounts:
    /// - reputation_account: Agent's reputation account
    #[access_control(reputation_exists(&ctx))]
    pub fn get_reputation(ctx: Context<GetReputation>) -> Result<ReputationScoreReturn> {
        let reputation = &ctx.accounts.reputation_account;
        
        Ok(ReputationScoreReturn {
            agent: reputation.agent,
            total_reviews: reputation.total_reviews,
            average_rating: reputation.average_rating,
            reputation_score: reputation.reputation_score,
            on_time_percentage: reputation.on_time_percentage,
        })
    }
}

// ========== Helper Functions ==========

fn calculate_score(
    average_rating: f64,
    on_time_percentage: f64,
    total_reviews: u32,
) -> f64 {
    // Normalize to 0-1
    let rating_norm = average_rating / 5.0;
    let on_time_norm = on_time_percentage / 100.0;
    
    // Volume bonus (diminishing returns)
    let volume_norm = (total_reviews as f64 / 100.0).min(1.0);
    
    // Weighted average: 40% rating, 30% on-time, 30% volume
    let score = (rating_norm * 0.4 + on_time_norm * 0.3 + volume_norm * 0.3) * 100.0;
    
    (score * 10.0).round() / 10.0 // Round to 1 decimal
}

// ========== Account Structures ==========

#[account]
pub struct ReputationAccount {
    pub agent: Pubkey,           // Agent's wallet address
    pub total_reviews: u32,       // Total reviews received
    pub average_rating: f64,      // Average rating (1-5)
    pub on_time_percentage: f64,  // On-time completion percentage
    pub reputation_score: f64,    // Calculated reputation score (0-100)
    pub positive_votes: u32,      // Total positive votes on reviews
    pub negative_votes: u32,     // Total negative votes on reviews
    pub review_count: u32,        // Number of reviews in list
    pub created_at: i64,         // Account creation timestamp
    pub updated_at: i64,          // Last update timestamp
}

impl ReputationAccount {
    pub const LEN: usize = 8 + 32 + 4 + 8 + 8 + 8 + 4 + 4 + 4 + 8 + 8;
}

#[account]
pub struct ReviewAccount {
    pub review_id: [u8; 32],          // Unique review identifier
    pub provider: Pubkey,              // Agent being reviewed
    pub reviewer: Pubkey,              // Account submitting review
    pub rating: u8,                    // Rating 1-5
    pub completed_on_time: bool,       // Whether task was on time
    pub comment_hash: [u8; 32],        // Hash of review comment
    pub positive_votes: u32,          // Upvotes
    pub negative_votes: u32,           // Downvotes
    pub timestamp: i64,                // Review timestamp
}

impl ReviewAccount {
    pub const LEN: usize = 8 + 32 + 32 + 32 + 1 + 1 + 32 + 4 + 4 + 8;
}

#[account]
pub struct ReviewListAccount {
    pub agent: Pubkey,              // Agent whose reviews are listed
    pub reviews: [Pubkey; MAX_REVIEWS_PER_AGENT as usize],  // Array of review PDAs
    pub count: u32,                 // Number of reviews in list
    pub created_at: i64,           // Account creation timestamp
    pub updated_at: i64,           // Last update timestamp
}

impl ReviewListAccount {
    pub const LEN: usize = 8 + 32 + (32 * MAX_REVIEWS_PER_AGENT as usize) + 4 + 8 + 8;
}

// ========== Return Structs =========-

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct ReputationScoreReturn {
    pub agent: Pubkey,
    pub total_reviews: u32,
    pub average_rating: f64,
    pub reputation_score: f64,
    pub on_time_percentage: f64,
}

// ========== Events ==========

#[event]
pub struct ReputationInitialized {
    pub agent: Pubkey,
    pub reputation_score: f64,
}

#[event]
pub struct ReviewSubmitted {
    pub review_id: [u8; 32],
    pub provider: Pubkey,
    pub reviewer: Pubkey,
    pub rating: u8,
}

#[event]
pub struct ScoreUpdated {
    pub agent: Pubkey,
    pub new_score: f64,
}

#[event]
pub struct ReviewVoted {
    pub review_id: [u8; 32],
    pub voter: Pubkey,
    pub vote_up: bool,
}

// ========== Contexts ==========

#[derive(Accounts)]
pub struct InitializeReputation<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(
        init,
        payer = payer,
        seeds = [REPUTATION_SEED, agent.key().as_ref()],
        bump,
        space = ReputationAccount::LEN
    )]
    pub reputation_account: Account<'info, ReputationAccount>,
    /// CHECK: This is the agent being initialized
    pub agent: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(review_id: [u8; 32])]
pub struct SubmitReview<'info> {
    #[account(mut)]
    pub reviewer: Signer<'info>,
    /// CHECK: Provider being reviewed
    pub provider: AccountInfo<'info>,
    #[account(
        mut,
        seeds = [REPUTATION_SEED, provider.key().as_ref()],
        bump,
    )]
    pub reputation_account: Account<'info, ReputationAccount>,
    #[account(
        init,
        payer = reviewer,
        seeds = [REVIEW_SEED, &review_id],
        bump,
        space = ReviewAccount::LEN
    )]
    pub review_account: Account<'info, ReviewAccount>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateScore<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        mut,
        seeds = [REPUTATION_SEED, reputation.agent.as_ref()],
        bump,
    )]
    pub reputation_account: Account<'info, ReputationAccount>,
}

#[derive(Accounts)]
#[instruction(review_id: [u8; 32])]
pub struct VoteReview<'info> {
    #[account(mut)]
    pub voter: Signer<'info>,
    #[account(
        mut,
        seeds = [REVIEW_SEED, &review_id],
        bump,
    )]
    pub review_account: Account<'info, ReviewAccount>,
}

#[derive(Accounts)]
pub struct GetReputation<'info> {
    #[account(
        seeds = [REPUTATION_SEED, reputation.agent.as_ref()],
        bump,
    )]
    pub reputation_account: Account<'info, ReputationAccount>,
}

// ========== Access Controls ==========

fn not_initialized(ctx: &Context<InitializeReputation>) -> Result<()> {
    let account = &ctx.accounts.reputation_account;
    require!(
        account.agent == Pubkey::default() || account.updated_at == 0,
        ReputationError::AlreadyInitialized
    );
    Ok(())
}

fn reputation_exists<T>(ctx: &Context<T>) -> Result<()> {
    let account = &ctx.accounts.reputation_account;
    require!(account.updated_at > 0, ReputationError::ReputationNotFound);
    Ok(())
}

fn review_exists<T>(ctx: &Context<T>) -> Result<()> {
    let account = &ctx.accounts.review_account;
    require!(account.timestamp > 0, ReviewError::ReviewNotFound);
    Ok(())
}

// ========== Errors ==========

#[error_code]
pub enum ReputationError {
    #[msg("Reputation account already initialized")]
    AlreadyInitialized,
    #[msg("Reputation account not found")]
    ReputationNotFound,
    #[msg("Invalid reputation score")]
    InvalidScore,
    #[msg("Unauthorized access")]
    Unauthorized,
}

#[error_code]
pub enum ReviewError {
    #[msg("Review not found")]
    ReviewNotFound,
    #[msg("Invalid rating (must be 1-5)")]
    InvalidRating,
    #[msg("Review list is full")]
    ReviewListFull,
    #[msg("Vote overflow")]
    VoteOverflow,
}
