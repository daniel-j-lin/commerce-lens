from __future__ import annotations

import re
from pathlib import Path


README = Path(__file__).resolve().parents[2] / "README.md"
ZH_HEADING = "# 繁體中文"
MARKER_RE = re.compile(r"<!-- parity: ([a-z0-9-]+) -->")
LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")
BASH_RE = re.compile(r"```bash\n(.*?)\n```", re.DOTALL)


EXPECTED_MARKERS = [
    "product-positioning",
    "why-different",
    "governed-coverage",
    "coverage-ux",
    "retained-evidence",
    "governed-refusal",
    "public-scope",
    "how-it-works",
    "quick-start",
    "schema-mapping",
    "coverage-example",
    "retention-example",
    "public-examples",
    "engineering",
    "validation-status",
    "safety-limitations",
    "license-release",
]


def _sections() -> tuple[str, str]:
    text = README.read_text(encoding="utf-8")
    assert text.count(ZH_HEADING) == 1
    english, traditional_chinese = text.split(ZH_HEADING, 1)
    assert english.index("## English") < english.index("<!-- parity: product-positioning -->")
    assert traditional_chinese.strip().startswith("<!-- parity: product-positioning -->")
    return english, traditional_chinese


def test_english_fully_precedes_traditional_chinese_and_markers_match() -> None:
    english, traditional_chinese = _sections()
    assert MARKER_RE.findall(english) == EXPECTED_MARKERS
    assert MARKER_RE.findall(traditional_chinese) == EXPECTED_MARKERS


def test_versions_install_commands_shell_blocks_and_links_match() -> None:
    english, traditional_chinese = _sections()
    assert english.count("0.2.0") == traditional_chinese.count("0.2.0")
    assert english.count("0.2.0") >= 4
    assert BASH_RE.findall(english) == BASH_RE.findall(traditional_chinese)
    assert set(LINK_RE.findall(english)) == set(LINK_RE.findall(traditional_chinese))


def test_supported_unsupported_and_limitation_sections_are_paired() -> None:
    english, traditional_chinese = _sections()
    for section in (english, traditional_chinese):
        assert "<!-- parity: public-scope -->" in section
        assert "<!-- parity: safety-limitations -->" in section
        assert "USER_DECLARED" in section
        assert "retained_complete" in section
        assert "ClaimDecision" in section
        assert "MetricState" in section and "ClaimState" in section
        assert "list" in section and "inspect" in section and "verify" in section
        assert "P01" in section and "NOT RUN" in section
        assert "P15" in section and "NOT PASS" in section


def test_language_independent_examples_remain_identical() -> None:
    english, traditional_chinese = _sections()
    required_blocks = (
        "Executed Result != Validated Result",
        "Insufficient evidence to conclude why Revenue declined.",
        "Order Number -> order_id",
        "Authority: USER_DECLARED; not independently verified by CommerceLens",
    )
    for block in required_blocks:
        assert english.count(block) == traditional_chinese.count(block) == 1
