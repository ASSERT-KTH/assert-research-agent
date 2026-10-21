"""CONVENTIONS.md stays executable: its examples pass the validators that enforce it.

The pre-registration example must satisfy both the hooks (during the work) and osaudit (after);
a spec example that a tool rejects, or two tools that disagree, is a defect.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

from _common import prereg_problems  # noqa: E402

CONVENTIONS = (ROOT / "CONVENTIONS.md").read_text(encoding="utf-8")
FRONT_MATTERS = re.findall(r"```toml\n(\+\+\+\n.*?\n\+\+\+)\n```", CONVENTIONS, re.DOTALL)


def osaudit_study():  # type: ignore[no-untyped-def]
    """osaudit's validator: mandatory in CI (it installs osaudit), skipped locally without it."""
    if os.environ.get("CI"):
        return importlib.import_module("osaudit._study")
    return pytest.importorskip("osaudit._study")


def example(mode: str) -> str:
    hits = [fm for fm in FRONT_MATTERS if f'mode = "{mode}"' in fm]
    assert len(hits) == 1, f"CONVENTIONS.md must hold exactly one {mode} front-matter example"
    return hits[0] + "\n"


def test_prereg_example_passes_hooks() -> None:
    assert prereg_problems(example("confirmatory")) == []


def test_prereg_example_passes_osaudit() -> None:
    study = osaudit_study()
    fm, why = study.front_matter(example("confirmatory"))
    assert fm is not None, why
    assert study.prereg_problems(fm) == []


def test_validators_agree_on_broken_examples() -> None:
    study = osaudit_study()
    good = example("confirmatory")
    for broken in (good.replace("alpha = 0.05", "alpha = 2"), good.replace("m = 3", "m = 0"),
                   good.replace('correction = "holm"', 'correction = "none"'),
                   good.replace("data_seen = false\n", "")):
        fm, _ = study.front_matter(broken)
        assert bool(prereg_problems(broken)) and bool(study.prereg_problems(fm)), broken


def test_exploration_log_example_parses() -> None:
    fm = tomllib.loads(example("exploratory").strip("+\n"))
    assert fm["mode"] == "exploratory"
    assert all(isinstance(p, str) for p in fm["holdout"] + fm["data_seen"])


def test_study_table_example_matches_hook_defaults(tmp_path: Path) -> None:
    from _common import study

    block = re.search(r"```toml\n(schema = [^\n]*\n\n\[study\]\n.*?)```", CONVENTIONS, re.DOTALL)
    assert block, "CONVENTIONS.md must show the [study] table"
    (tmp_path / "audit.toml").write_text(block.group(1))
    s = study(str(tmp_path))
    assert (s.prereg, s.explore, s.experiments, s.results) == ("prereg", "explore", "experiments", "results")
    assert s.report == ["REPORT.md", "NOTES.md", "README.md"]
    assert s.audit_problem is None
    jsonschema().validate(tomllib.loads(block.group(1)), schema("audit-v1"))


SCHEMA_DIR = ROOT / "schemas"
BASE = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/"


def jsonschema():  # type: ignore[no-untyped-def]
    """The JSON Schema validator: mandatory in CI, skipped locally without it."""
    if os.environ.get("CI"):
        return importlib.import_module("jsonschema")
    return pytest.importorskip("jsonschema")


def schema(name: str) -> dict:
    import json

    return json.loads((SCHEMA_DIR / f"{name}.json").read_text())


@pytest.mark.parametrize("path", sorted(SCHEMA_DIR.glob("*.json")), ids=lambda p: p.stem)
def test_schema_points_to_itself(path: Path) -> None:
    import json

    s = json.loads(path.read_text())
    url = BASE + path.name
    assert s["$id"] == url and s["properties"]["schema"]["const"] == url and "schema" in s["required"]
    jsonschema().Draft202012Validator.check_schema(s)


@pytest.mark.parametrize("mode, name", [("confirmatory", "prereg-v1"), ("exploratory", "exploration-log-v1")])
def test_front_matter_examples_validate(mode: str, name: str) -> None:
    fm = tomllib.loads(example(mode).strip().strip("+").strip())
    jsonschema().validate(fm, schema(name))
    del fm["schema"]
    with pytest.raises(jsonschema().ValidationError):  # mandatory
        jsonschema().validate(fm, schema(name))


def test_provenance_example_validates() -> None:
    import json

    block = re.search(r'```json\n("provenance": \{.*?\n\})\n```', CONVENTIONS, re.DOTALL)
    assert block, "CONVENTIONS.md must show the provenance block"
    jsonschema().validate(json.loads("{" + block.group(1) + "}")["provenance"], schema("provenance-v1"))


def test_prereg_schema_and_hook_agree_on_m_without_correction() -> None:
    fm = tomllib.loads(example("confirmatory").strip().strip("+").strip())
    fm["correction"] = "none"
    with pytest.raises(jsonschema().ValidationError):
        jsonschema().validate(fm, schema("prereg-v1"))
