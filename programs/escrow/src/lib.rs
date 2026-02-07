//! USDC Escrow Program for Agent Skill Rentals
//!
//! - Provider creates escrow with terms
//! - Renter accepts and funds (USDC locked)
//! - Task completes → funds released to provider
//! - Cancel → funds refunded to renter

use anchor_lang::prelude::*;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};

declare_id!("8uBMA8S33eGFMRA677Y1gPvmnBGUjFtdwxf2A8JufpA3");

const ESCROW_SEED: &[u8] = b"escrow";

#[program]
pub mod escrow {
    use super::*;

    /// Initialize a new escrow for a skill rental
    pub fn initialize_escrow(ctx: Context<InitializeEscrow>, terms: EscrowTerms) -> Result<()> {
        require!(
            ctx.accounts.escrow_account.state == EscrowState::Created
                || ctx.accounts.escrow_account.state == EscrowState::default(),
            EscrowError::InvalidState
        );
        let escrow = &mut ctx.accounts.escrow_account;

        escrow.provider = ctx.accounts.provider.key();
        escrow.renter = Pubkey::default();
        escrow.token_mint = ctx.accounts.token_mint.key();
        escrow.provider_token_account = ctx.accounts.provider_token_account.key();
        escrow.terms = terms;
        escrow.state = EscrowState::Created;
        escrow.created_at = Clock::get()?.unix_timestamp;

        Ok(())
    }

    /// Accept escrow and fund it (USDC transferred from renter to escrow ATA)
    pub fn accept_escrow(ctx: Context<AcceptEscrow>, amount: u64) -> Result<()> {
        require!(ctx.accounts.escrow_account.state == EscrowState::Created, EscrowError::InvalidState);
        let escrow = &mut ctx.accounts.escrow_account;
        escrow.renter = ctx.accounts.renter.key();
        escrow.amount = amount;
        escrow.state = EscrowState::Funded;

        let cpi_accounts = Transfer {
            from: ctx.accounts.renter_token_account.to_account_info(),
            to: ctx.accounts.escrow_token_account.to_account_info(),
            authority: ctx.accounts.renter.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(CpiContext::new(cpi_program, cpi_accounts), amount)?;

        Ok(())
    }

    /// Complete task and release USDC to provider
    pub fn complete_task(ctx: Context<CompleteTask>) -> Result<()> {
        require!(ctx.accounts.escrow_account.state == EscrowState::Funded, EscrowError::InvalidState);
        let escrow = &mut ctx.accounts.escrow_account;
        escrow.state = EscrowState::Completed;
        escrow.completed_at = Clock::get()?.unix_timestamp;
        let amount = escrow.amount;
        let provider = escrow.provider;

        let seeds = &[ESCROW_SEED, provider.as_ref(), &[ctx.bumps.escrow_account]];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.provider_token_account.to_account_info(),
            authority: ctx.accounts.escrow_account.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(
            CpiContext::new_with_signer(cpi_program, cpi_accounts, signer),
            amount,
        )?;

        Ok(())
    }

    /// Cancel escrow and refund USDC to renter
    pub fn cancel_escrow(ctx: Context<CancelEscrow>) -> Result<()> {
        require!(ctx.accounts.escrow_account.state == EscrowState::Funded, EscrowError::InvalidState);
        let escrow = &mut ctx.accounts.escrow_account;
        escrow.state = EscrowState::Cancelled;
        escrow.cancelled_at = Clock::get()?.unix_timestamp;
        let amount = escrow.amount;
        let provider = escrow.provider;

        let seeds = &[ESCROW_SEED, provider.as_ref(), &[ctx.bumps.escrow_account]];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.renter_token_account.to_account_info(),
            authority: ctx.accounts.escrow_account.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(
            CpiContext::new_with_signer(cpi_program, cpi_accounts, signer),
            amount,
        )?;

        Ok(())
    }

    /// Check if escrow has timed out
    pub fn check_timeout(ctx: Context<CheckTimeout>) -> Result<bool> {
        require!(ctx.accounts.escrow_account.state == EscrowState::Funded, EscrowError::InvalidState);
        let escrow = &ctx.accounts.escrow_account;
        let now = Clock::get()?.unix_timestamp;
        Ok(now >= escrow.created_at + escrow.terms.duration_seconds)
    }
}

// ========== Account Structures ==========

#[account]
pub struct EscrowAccount {
    pub provider: Pubkey,
    pub renter: Pubkey,
    pub token_mint: Pubkey,
    pub provider_token_account: Pubkey,
    pub escrow_token_account: Pubkey,
    pub terms: EscrowTerms,
    pub state: EscrowState,
    pub amount: u64,
    pub created_at: i64,
    pub completed_at: i64,
    pub cancelled_at: i64,
}

impl EscrowAccount {
    pub const LEN: usize = 8 + 32 * 5 + 8 + 64 + 8 + 8 + 256 + 64 + 1 + 8 * 4;
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug)]
pub struct EscrowTerms {
    pub skill_name: String,
    pub duration_seconds: i64,
    pub price_usdc: u64,
    pub metadata_uri: String,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug, PartialEq, Default)]
pub enum EscrowState {
    #[default]
    Created,
    Funded,
    Completed,
    Cancelled,
}

// ========== Contexts ==========

#[derive(Accounts)]
pub struct InitializeEscrow<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        init,
        payer = provider,
        seeds = [ESCROW_SEED, provider.key().as_ref()],
        bump,
        space = EscrowAccount::LEN
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    pub token_mint: Account<'info, token::Mint>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = provider
    )]
    pub provider_token_account: Account<'info, TokenAccount>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
}

#[derive(Accounts)]
pub struct AcceptEscrow<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow_account.provider.as_ref()],
        bump,
        has_one = provider_token_account,
        has_one = token_mint,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    /// Provider's token account (must match escrow_account.provider_token_account)
    pub provider_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    #[account(
        init_if_needed,
        payer = renter,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = renter,
    )]
    pub renter_token_account: Account<'info, TokenAccount>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
}

#[derive(Accounts)]
pub struct CompleteTask<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow_account.provider.as_ref()],
        bump,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account.provider,
    )]
    pub provider_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct CancelEscrow<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow_account.provider.as_ref()],
        bump,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account.renter,
    )]
    pub renter_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct CheckTimeout<'info> {
    #[account(
        seeds = [ESCROW_SEED, escrow_account.provider.as_ref()],
        bump,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
}

// ========== Errors ==========

#[error_code]
pub enum EscrowError {
    #[msg("Invalid escrow state for this operation")]
    InvalidState,
    #[msg("Timeout has not elapsed yet")]
    TimeoutNotElapsed,
    #[msg("Unauthorized caller")]
    Unauthorized,
    #[msg("Insufficient funds")]
    InsufficientFunds,
}
