"""P9 minimum physical fixture runner."""

from importlib import import_module

from commerce_lens.fixture_runner.cases import FixtureCase, FixtureCaseError, discover_cases, load_case

__all__ = (
    "CaseRunResult",
    "FixtureCase",
    "FixtureCaseError",
    "discover_cases",
    "load_case",
    "run_case",
    "run_suite",
)


def __getattr__(name: str):
    if name in {"CaseRunResult", "run_case", "run_suite"}:
        runner = import_module("commerce_lens.fixture_runner.runner")
        return getattr(runner, name)
    raise AttributeError(name)
