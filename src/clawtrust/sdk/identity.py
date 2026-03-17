try:
    from trustyclaw.sdk.identity import *  # type: ignore # noqa: F401,F403
except ModuleNotFoundError:
    from src.trustyclaw.sdk.identity import *  # type: ignore # noqa: F401,F403
