"""Compatibility SDK package for legacy clawtrust.sdk imports."""

try:
    from trustyclaw.sdk import *  # type: ignore # noqa: F401,F403
except ModuleNotFoundError:
    from src.trustyclaw.sdk import *  # type: ignore # noqa: F401,F403
