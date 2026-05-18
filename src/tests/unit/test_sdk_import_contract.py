"""Regression tests for README-documented SDK import contract."""


def test_readme_import_contract_modules_are_importable() -> None:
    """README examples should continue importing from these public SDK modules."""
    from trustyclaw.sdk.escrow_contract import get_escrow_client
    from trustyclaw.sdk.review_system import get_review_service
    from trustyclaw.sdk.solana import get_client
    from trustyclaw.sdk.usdc import get_usdc_client

    assert callable(get_client)
    assert callable(get_usdc_client)
    assert callable(get_escrow_client)
    assert callable(get_review_service)
