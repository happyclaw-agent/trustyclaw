try:
    from trustyclaw.sdk.reputation import *  # type: ignore # noqa: F401,F403
except ModuleNotFoundError:
    from src.trustyclaw.sdk.reputation import *  # type: ignore # noqa: F401,F403
