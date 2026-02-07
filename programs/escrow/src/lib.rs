use anchor_lang::prelude::*;

declare_id!("ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF");

const ESCROW_SEED: &[u8] = b"escrow";

#[program]
pub mod escrow {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, data: EscrowData) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.provider = data.provider;
        escrow.renter = data.renter;
        escrow.amount = data.amount;
        escrow.state = 0; // 0 = created
        escrow.timestamp = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn fund(ctx: Context<Fund>, amount: u64) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.renter = ctx.accounts.renter.key();
        escrow.amount = amount;
        escrow.state = 1; // 1 = funded
        Ok(())
    }

    pub fn release(ctx: Context<Release>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.state = 2; // 2 = released
        Ok(())
    }

    pub fn refund(ctx: Context<Refund>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.state = 3; // 3 = refunded
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        init,
        payer = provider,
        seeds = [ESCROW_SEED, provider.key().as_ref()],
        bump,
        space = 200
    )]
    pub escrow: Account<'info, Escrow>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Fund<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow: Account<'info, Escrow>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Release<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
        has_one = renter,
    )]
    pub escrow: Account<'info, Escrow>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Refund<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow: Account<'info, Escrow>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Escrow {
    pub provider: Pubkey,
    pub renter: Pubkey,
    pub amount: u64,
    pub state: u8,
    pub timestamp: i64,
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct EscrowData {
    pub provider: Pubkey,
    pub renter: Pubkey,
    pub amount: u64,
}
