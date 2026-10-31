"""Smoke tests for stack_health_summary parsing (run: pytest scripts/)."""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import stack_health_summary as shs

ARRAY = '[{"Service": "web", "State": "running"}, {"Service": "db", "State": "exited"}]'
JSON_LINES = '{"Service": "web", "State": "running"}\n{"Service": "db", "State": "exited"}\n'
EXPECTED = "web: running\ndb: exited"


@pytest.mark.parametrize("text", [ARRAY, JSON_LINES])
def test_array_and_json_lines_render_the_same(text):
    assert shs.render(shs.parse_ps_json(text)) == EXPECTED


def test_single_object():
    rows = shs.parse_ps_json('{"Service": "web", "State": "running"}')
    assert shs.render(rows) == "web: running"


@pytest.mark.parametrize("text", ["", "  \n", "{}", "[]"])
def test_empty_stack(text):
    assert shs.parse_ps_json(text) == []


def test_missing_keys_fall_back():
    assert shs.render([{"Name": "moor-web-1"}, {}]) == "moor-web-1: unknown\n?: unknown"


def test_garbage_raises():
    with pytest.raises(ValueError):
        shs.parse_ps_json("not json")
    with pytest.raises(ValueError):
        shs.parse_ps_json("42")
    with pytest.raises(ValueError):
        shs.render(["web"])


def test_command_failure_exits_nonzero(monkeypatch, capsys):
    def boom(*a, **k):
        raise subprocess.CalledProcessError(1, a[0])

    monkeypatch.setattr(shs.subprocess, "check_output", boom)
    assert shs.main() == 1
    out, err = capsys.readouterr()
    assert out == "" and "stack_health_summary:" in err


def test_unparseable_output_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(shs.subprocess, "check_output", lambda *a, **k: "Extra}{")
    assert shs.main() == 1
    assert "stack_health_summary:" in capsys.readouterr().err


def test_uses_argv_list_not_shell(monkeypatch):
    seen = {}

    def fake(cmd, **kw):
        seen["cmd"], seen["kw"] = cmd, kw
        return ARRAY

    monkeypatch.setattr(shs.subprocess, "check_output", fake)
    assert shs.summary() == EXPECTED
    assert isinstance(seen["cmd"], list) and not seen["kw"].get("shell")
