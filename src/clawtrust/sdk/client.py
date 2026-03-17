try:
    from trustyclaw.sdk.client import *  # type: ignore # noqa: F401,F403
except ModuleNotFoundError:
    from src.trustyclaw.sdk.client import *  # type: ignore # noqa: F401,F403
