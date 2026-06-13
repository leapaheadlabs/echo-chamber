"""Shared test fixtures for ECHO CHAMBER."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _isolate_env() -> None:
    """Ensure tests never touch real credentials."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DB_PASSWORD"] = "echo" + "_test" + "_password"
    os.environ.setdefault("OPENAI_API_KEY", "sk-test" + "-not-real")
