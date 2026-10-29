import pytest
from fastapi import HTTPException

from app.api.v1.cases import ALLOWED_TRANSITIONS


def test_case_transition_graph():
    assert "under_review" in ALLOWED_TRANSITIONS["pending"]
    assert "resolved" in ALLOWED_TRANSITIONS["under_review"]
    assert ALLOWED_TRANSITIONS["dismissed"] == set()
