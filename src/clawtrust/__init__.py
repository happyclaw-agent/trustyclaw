"""Compatibility package for legacy clawtrust imports."""

try:  # top-level package import style (e.g. sys.path includes src/)
    from trustyclaw import *  # type: ignore # noqa: F401,F403
except ModuleNotFoundError:  # namespace style import (e.g. import src.clawtrust)
    from src.trustyclaw import *  # type: ignore # noqa: F401,F403
