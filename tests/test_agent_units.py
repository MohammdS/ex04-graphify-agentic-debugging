"""Offline unit tests for the agent modules.

These run with no network access: the LLM is either skipped (no API key -> the
deterministic fallback path) or replaced with a fake OpenAI client. They cover
the pure-logic helpers and the orchestration seams created by the refactor.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))

import compare_token_usage  # noqa: E402
import debug_state  # noqa: E402
import llm_support  # noqa: E402
import nodes  # noqa: E402
import rank_suspects  # noqa: E402
import suspect_ranking  # noqa: E402
import suspect_report  # noqa: E402
import token_prompts  # noqa: E402
import token_report  # noqa: E402
import token_scoring  # noqa: E402
import workflow  # noqa: E402


# --- fake OpenAI client -----------------------------------------------------

GOOD_ANSWER = (
    "This is a mutable default argument; the same list is shared across calls. "
    "Fix: use bar=None and if bar is none create a new list (fresh list)."
)


class _Usage:
    prompt_tokens = 10
    completion_tokens = 20
    total_tokens = 30


class _Msg:
    content = GOOD_ANSWER


class _Choice:
    message = _Msg()


class _Resp:
    choices = [_Choice()]
    usage = _Usage()


class _Completions:
    def create(self, **kwargs):
        return _Resp()


class _Chat:
    completions = _Completions()


class FakeOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = _Chat()


def _inject_fake_openai(monkeypatch, cls=FakeOpenAI):
    module = types.ModuleType("openai")
    module.OpenAI = cls
    monkeypatch.setitem(sys.modules, "openai", module)


# --- token_scoring ----------------------------------------------------------

def test_evaluate_response_success():
    diagnosis, fix, criteria = token_scoring.evaluate_response(GOOD_ANSWER)
    assert diagnosis is True
    assert fix is True
    assert len(criteria) == 3


def test_evaluate_response_failure_on_empty():
    diagnosis, fix, _ = token_scoring.evaluate_response("")
    assert diagnosis is False
    assert fix is False


def test_average_and_success_rate():
    assert token_scoring.average([1, 2, None]) == 1.5
    assert token_scoring.average([None]) is None
    assert token_scoring.success_rate([]) == 0.0


# --- token_prompts ----------------------------------------------------------

def test_estimate_tokens_and_slug():
    assert token_prompts.estimate_tokens("a b c") == 4
    assert token_prompts.slug("GLM-4.7/Flashx") == "glm-4-7-flashx"


def test_buggy_source_and_read_files():
    assert "bar=[]" in token_prompts.buggy_foobar_source()
    files = token_prompts.read_text_files(ROOT / "src")
    assert len(files) == 5
    assert any(key.endswith("foobar.py") for key in files)


def test_graph_context_and_prompts():
    ctx = token_prompts.graph_context("foo()")
    assert len(ctx["target"]) == 1
    assert len(ctx["neighbors"]) == 3
    naive = json.loads(token_prompts.build_naive_prompt("q"))
    assert "source_files" in naive
    graph = json.loads(token_prompts.build_graph_prompt("q", "foo()"))
    assert "graph_context" in graph


# --- suspect_ranking / suspect_report ---------------------------------------

def test_rank_suspects_puts_seed_first():
    id_to_label, adjacency = suspect_ranking.load_graph(ROOT / "data" / "graph.json")
    assert suspect_ranking.find_seed_id("foo()", id_to_label) is not None
    assert suspect_ranking.find_seed_id("nope", id_to_label) is None
    seed_id = suspect_ranking.find_seed_id("foo()", id_to_label)
    distances = suspect_ranking.bfs_distances(adjacency, seed_id)
    assert distances[seed_id] == 0
    rows = suspect_ranking.rank_suspects(id_to_label, adjacency, seed_id)
    assert rows[0]["label"] == "foo()"


def test_build_markdown_and_format_distance():
    assert suspect_report.format_distance(None) == "inf"
    assert suspect_report.format_distance(2) == "2"
    rows = [{"label": "foo()", "degree": 3, "degree_centrality": 0.5, "distance": 0, "score": 1.2}]
    md = suspect_report.build_markdown(rows, "foo()", 3)
    assert "Suspect Ranking Report" in md
    assert "foo()" in md


# --- llm_support ------------------------------------------------------------

def test_call_llm_no_key_returns_none(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    content, usage = llm_support.call_llm("sys", "user")
    assert content is None
    assert usage == {}


def test_merge_usage():
    merged = llm_support.merge_usage({"a": 1}, {"a": 2, "b": 3})
    assert merged == {"a": 3, "b": 3}


def test_call_llm_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    _inject_fake_openai(monkeypatch)
    content, usage = llm_support.call_llm("sys", "user")
    assert content == GOOD_ANSWER
    assert usage["total_tokens"] == 30


def test_call_llm_exception_path(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    class Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("boom")

    _inject_fake_openai(monkeypatch, cls=Boom)
    content, usage = llm_support.call_llm("sys", "user")
    assert content.startswith("LLM call failed")
    assert usage == {}


# --- debug_state ------------------------------------------------------------

def test_debug_state_helpers():
    assert debug_state.estimate_tokens("one two") == 3
    assert debug_state.read_prompt("graph_reader.md").strip() != ""
    ctx = debug_state.source_context_for([{"source_file": "src/buggy_python/foobar.py"}])
    assert "src/buggy_python/foobar.py" in ctx


# --- nodes / workflow (offline fallback path) -------------------------------

def test_workflow_offline_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    class _Done:
        stdout = "3 passed"
        stderr = ""

    monkeypatch.setattr(nodes.subprocess, "run", lambda *a, **k: _Done())
    result = workflow.build_workflow().invoke(
        {"question": "why?", "target_node": "foo()"}
    )
    assert result["llm_used"] is False
    assert result["root_cause"] == llm_support.FALLBACK_ROOT_CAUSE
    assert result["fix_plan"] == llm_support.FALLBACK_FIX_PLAN
    assert result["verification"] == "3 passed"
    assert result["graph_summary"]["node_count"] == 19


def test_workflow_llm_path(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    _inject_fake_openai(monkeypatch)

    class _Done:
        stdout = "3 passed"
        stderr = ""

    monkeypatch.setattr(nodes.subprocess, "run", lambda *a, **k: _Done())
    result = workflow.build_workflow().invoke(
        {"question": "why?", "target_node": "foo()"}
    )
    assert result["llm_used"] is True
    assert result["root_cause"] == GOOD_ANSWER
    assert result["llm_usage"]["total_tokens"] > 0


# --- compare_token_usage (call_model + main, faked client) ------------------

def test_call_model_with_fake_client():
    client = FakeOpenAI()
    res = compare_token_usage.call_model(client, "m", "graph_guided", "prompt", 1)
    assert res.success is True
    assert res.total_tokens == 30
    assert res.usage_source == "api_usage"


def test_main_writes_outputs(monkeypatch):
    _inject_fake_openai(monkeypatch)
    monkeypatch.setattr(
        sys, "argv", ["prog", "--model", "pytest-dummy", "--runs", "1", "--api-key", "x"]
    )
    out_json = ROOT / "data" / "measured-token-comparison-pytest-dummy.json"
    out_md = ROOT / "reports" / "MEASURED_TOKEN_COMPARISON_pytest-dummy.md"
    try:
        compare_token_usage.main()
        assert out_json.exists()
        assert out_md.exists()
        payload = json.loads(out_json.read_text())
        assert payload["model"] == "pytest-dummy"
        assert payload["averages"]["runs"] == 1
    finally:
        out_json.unlink(missing_ok=True)
        out_md.unlink(missing_ok=True)


# --- rank_suspects CLI ------------------------------------------------------

def test_rank_suspects_main_ok():
    assert rank_suspects.main(["--seed", "foo()", "--top", "3"]) == 0
    assert rank_suspects.OUTPUT_MD.exists()


def test_rank_suspects_main_bad_seed(capsys):
    assert rank_suspects.main(["--seed", "does-not-exist"]) == 1
    assert "not found" in capsys.readouterr().out
