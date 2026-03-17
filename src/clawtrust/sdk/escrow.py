try:
    from trustyclaw.sdk.escrow import *  # type: ignore # noqa: F401,F403
except ModuleNotFoundError:
    from src.trustyclaw.sdk.escrow import *  # type: ignore # noqa: F401,F403
