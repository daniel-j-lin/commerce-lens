from __future__ import annotations

import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FACT_RE = re.compile(r"<!-- fact: ([^>]+) -->")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
BASH_RE = re.compile(r"```bash\n(.*?)\n```", re.DOTALL)
ANCHORS = (
    '<a id="english"></a>',
    '<a id="traditional-chinese"></a>',
    '<a id="simplified-chinese"></a>',
)
FLOW_ASSETS = (
    "docs/assets/readme/commerce-lens-flow-en.svg",
    "docs/assets/readme/commerce-lens-flow-zh-TW.svg",
    "docs/assets/readme/commerce-lens-flow-zh-CN.svg",
)
TOPOLOGY_IDS = {
    "input", "mapping", "calculation", "decomposition", "hypothesis",
    "admission", "refusal", "diagnostic", "validation", "explanation",
}


def _text() -> str:
    return README.read_text(encoding="utf-8")


def _sections() -> tuple[str, str, str, str]:
    text = _text()
    assert all(text.count(anchor) == 1 for anchor in ANCHORS)
    preface, tail = text.split(ANCHORS[0], 1)
    english, tail = tail.split(ANCHORS[1], 1)
    traditional, simplified = tail.split(ANCHORS[2], 1)
    return preface, english, traditional, simplified


def test_language_navigation_and_sections_are_stable() -> None:
    preface, english, traditional, simplified = _sections()
    assert "[English](#english)" in preface
    assert "[繁體中文](#traditional-chinese)" in preface
    assert "[简体中文](#simplified-chinese)" in preface
    assert english.lstrip().startswith("## English")
    assert traditional.lstrip().startswith("## 繁體中文")
    assert simplified.lstrip().startswith("## 简体中文")


def test_material_facts_and_commands_match_across_all_languages() -> None:
    _, *sections = _sections()
    facts = [FACT_RE.findall(section) for section in sections]
    commands = [BASH_RE.findall(section) for section in sections]
    assert facts[0] == facts[1] == facts[2]
    assert commands[0] == commands[1] == commands[2]
    assert len(commands[0]) == 2


def test_all_languages_preserve_diagnostic_values_limits_and_public_boundary() -> None:
    _, *sections = _sections()
    required = (
        "v0.3.0", "18%", "8", "4", "-1.0", "rho <= -0.50",
        "CRITERION_MET", "ClaimDecision", "Finding",
        "product_composition_association",
        "weekly_product_presence_revenue_association@1.0.0",
        "product_id", "Revenue", "P00", "PASS", "P01", "NOT RUN", "P15", "NOT PASS",
    )
    for section in sections:
        assert all(value in section for value in required)
        assert "repository/MVP" in section
        assert "public" in section.lower() or "公開" in section or "公开" in section
        assert "seasonality" in section.lower() or "季節性" in section or "季节性" in section
        assert "external" in section.lower() or "外部" in section


def test_no_stale_universal_diagnostic_unavailability_or_causal_claim() -> None:
    text = _text()
    assert "unsupported=diagnostic" not in text
    assert "| Calculate Revenue | Explain why Revenue changed |" not in text
    prohibited = (
        "product composition caused Revenue decline",
        "product composition is the primary cause",
        "product composition is the sole cause",
        "statistically significant",
        "proves a causal effect",
    )
    assert not any(phrase.lower() in text.lower() for phrase in prohibited)


def test_links_release_note_and_versions_resolve() -> None:
    for target in LINK_RE.findall(_text()):
        if target.startswith(("#", "http://", "https://")):
            continue
        assert (ROOT / target.split("#", 1)[0]).exists(), target
    assert (ROOT / "release-notes/v0.3.1.md").exists()
    assert 'version = "0.3.1"' in (ROOT / "pyproject.toml").read_text()
    assert '__version__ = "0.3.1"' in (ROOT / "src/commerce_lens/__init__.py").read_text()
    assert json.loads((ROOT / ".codex-plugin/plugin.json").read_text())["version"] == "0.3.1"


def test_three_flow_assets_are_valid_and_share_topology() -> None:
    assert set(FLOW_ASSETS) <= set(LINK_RE.findall(_text()))
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    observed = []
    for relative in FLOW_ASSETS:
        root = ET.parse(ROOT / relative).getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib.get("role") == "img"
        assert root.attrib.get("aria-labelledby") == "title desc"
        assert root.find("svg:title", namespace) is not None
        assert root.find("svg:desc", namespace) is not None
        ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}
        assert TOPOLOGY_IDS <= ids
        observed.append(ids & TOPOLOGY_IDS)
    assert observed[0] == observed[1] == observed[2]
