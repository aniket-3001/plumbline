"""Tests for Layer 2 -- the only place a model is allowed to speak.

The rules being tested here are the fence around that model. Without them a
hallucinated cell reference reaches an analyst's audit report, which is worse than
saying nothing: it sends them chasing a cell that was never wrong.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import plumbline  # noqa: F401
from plumbline.agent import (
    SYSTEM_PROMPT,
    Interpretation,
    _render_user_prompt,
    _strip_fence,
    build_context,
    interpret,
)
from plumbline.audit import audit

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "tests" / "fixtures" / "quarterly_pl.xlsx"


@pytest.fixture(scope="module")
def finding():
    return audit(CLEAN, check_determinism=False).proved[0]


def stub(payload) -> callable:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return lambda system, user: text


class TestContext:
    def test_finds_the_labels_that_give_the_cell_meaning(self, finding):
        ctx = build_context(str(CLEAN), finding)
        assert ctx["row_label"] == "Total Opex"
        assert ctx["column_label"] == "Q2"

    def test_includes_row_peers(self, finding):
        ctx = build_context(str(CLEAN), finding)
        peers = {p["cell"] for p in ctx["row_peers"]}
        assert {"B11", "D11", "E11"} <= peers

    def test_excludes_the_cell_itself_from_peers(self, finding):
        ctx = build_context(str(CLEAN), finding)
        assert finding.cell not in {p["cell"] for p in ctx["row_peers"]}

    def test_stays_small(self, finding):
        """A whole sheet neither fits a context window nor helps."""
        prompt = _render_user_prompt(build_context(str(CLEAN), finding))
        assert len(prompt) < 2000

    def test_carries_the_proof_so_the_model_does_not_relitigate_it(self, finding):
        ctx = build_context(str(CLEAN), finding)
        assert "27000" in ctx["proof"] and "30000" in ctx["proof"]


class TestHallucinationGuard:
    def test_accepts_cells_present_in_the_context(self, finding):
        result = interpret(str(CLEAN), finding, stub({
            "intent": "Total operating expenses for Q2",
            "deliberate": False,
            "explanation": "Every other quarter sums three lines; Q2 sums two.",
            "cells_referenced": ["C8", "C10", "B11"],
        }))
        assert result.ok
        assert result.rejected_cells == []

    def test_rejects_an_invented_cell(self, finding):
        result = interpret(str(CLEAN), finding, stub({
            "intent": "x", "deliberate": False, "explanation": "y",
            "cells_referenced": ["ZZ999"],
        }))
        assert not result.ok
        assert result.rejected_cells == ["ZZ999"]
        assert "ZZ999" in result.error

    def test_one_bad_reference_invalidates_the_whole_interpretation(self, finding):
        """Partial trust is not a thing: if it invented one cell, drop the claim."""
        result = interpret(str(CLEAN), finding, stub({
            "intent": "x", "deliberate": False, "explanation": "y",
            "cells_referenced": ["C8", "QQ42"],
        }))
        assert not result.ok


class TestRobustness:
    def test_survives_a_model_outage(self, finding):
        def boom(system, user):
            raise ConnectionError("upstream down")

        result = interpret(str(CLEAN), finding, boom)
        assert not result.ok
        assert "ConnectionError" in result.error

    def test_survives_unparsable_output(self, finding):
        result = interpret(str(CLEAN), finding, stub("not json at all"))
        assert not result.ok
        assert "unparsable" in result.error

    def test_strips_markdown_fences(self):
        assert _strip_fence('```json\n{"a": 1}\n```') == '{"a": 1}'
        assert _strip_fence('{"a": 1}') == '{"a": 1}'

    def test_truncates_runaway_output(self, finding):
        result = interpret(str(CLEAN), finding, stub({
            "intent": "x" * 5000, "deliberate": None,
            "explanation": "y" * 5000, "cells_referenced": [],
        }))
        assert len(result.intent) <= 400
        assert len(result.explanation) <= 800


class TestPromptContract:
    def test_forbids_overturning_the_proof(self):
        """Recomputation decides errors. The model supplies intent only."""
        assert "NOT deciding whether this is an error" in SYSTEM_PROMPT

    def test_forbids_inventing_references(self):
        assert "Never invent a cell reference" in SYSTEM_PROMPT.replace("\\n", "")

    def test_permits_admitting_ignorance(self):
        """A model with no way to say 'unclear' will confabulate instead."""
        assert "do not indicate the intent" in SYSTEM_PROMPT


def test_interpretation_serialises():
    assert Interpretation(intent="i").to_dict()["intent"] == "i"
