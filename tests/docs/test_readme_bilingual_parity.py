from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
EN_ANCHOR = '<a id="english"></a>'
ZH_ANCHOR = '<a id="traditional-chinese"></a>'
FACT_RE = re.compile(r"<!-- fact: ([^>]+) -->")
LINK_RE = re.compile(r"!?(?:\[[^]]*\])\(([^)]+)\)")
BASH_RE = re.compile(r"```bash\n(.*?)\n```", re.DOTALL)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

EXPECTED_FACTS = [
    "inputs=csv,xlsx",
    "metrics=revenue,orders,aov,absolute-revenue-change",
    "unsupported=diagnostic,causal,predictive,prescriptive,revenue-change-percentage,product-category-contribution-ranking",
    "retention=temporary-default,opt-in,list-inspect-verify,plaintext,no-ttl,no-encryption,no-secure-erase",
    "release=v0.2.0,public,tag-v0.2.0",
    "validation=p00-pass-internal,p01-not-run,p15-not-pass",
]

FLOW_ASSETS = {
    "docs/assets/readme/commerce-lens-flow-en.svg",
    "docs/assets/readme/commerce-lens-flow-zh-TW.svg",
}


def _text() -> str:
    return README.read_text(encoding="utf-8")


def _sections() -> tuple[str, str, str]:
    text = _text()
    assert text.count(EN_ANCHOR) == 1
    assert text.count(ZH_ANCHOR) == 1
    preface, remainder = text.split(EN_ANCHOR, 1)
    english, traditional_chinese = remainder.split(ZH_ANCHOR, 1)
    return preface, english, traditional_chinese


def test_language_navigation_and_sections_are_stable() -> None:
    preface, english, traditional_chinese = _sections()
    assert "[English](#english)" in preface
    assert "[繁體中文](#traditional-chinese)" in preface
    assert english.lstrip().startswith("## English")
    assert traditional_chinese.lstrip().startswith("## 繁體中文")


def test_material_facts_match_without_requiring_literal_translation() -> None:
    _, english, traditional_chinese = _sections()
    assert FACT_RE.findall(english) == EXPECTED_FACTS
    assert FACT_RE.findall(traditional_chinese) == EXPECTED_FACTS


def test_install_and_retention_commands_match_exactly() -> None:
    _, english, traditional_chinese = _sections()
    assert BASH_RE.findall(english) == BASH_RE.findall(traditional_chinese)
    assert len(BASH_RE.findall(english)) == 2


def test_release_validation_and_synthetic_example_are_factually_paired() -> None:
    _, english, traditional_chinese = _sections()
    for section in (english, traditional_chinese):
        for value in (
            "v0.2.0",
            "12,000 USD",
            "10,800 USD",
            "-1,200 USD",
            "USER_DECLARED",
            "retained_complete",
            "P00",
            "PASS",
            "P01",
            "NOT RUN",
            "P15",
            "NOT PASS",
        ):
            assert value in section

    text = _text()
    stale_release_phrases = (
        "local release candidate only",
        "publication requires explicit authorization",
        "No tag, GitHub Release",
    )
    assert not any(phrase in text for phrase in stale_release_phrases)


def test_english_section_has_no_unexplained_chinese_prose() -> None:
    _, english, _ = _sections()
    assert CJK_RE.search(english) is None


def test_traditional_chinese_uses_localized_user_facing_explanations() -> None:
    _, _, traditional_chinese = _sections()
    for phrase in (
        "資料不完整時",
        "合成資料範例",
        "提出商務問題",
        "確認匯出資料是否完整",
        "資料不足時會停止回答",
        "保留在本機的資料是明文",
    ):
        assert phrase in traditional_chinese

    for old_english_block in (
        "Executed Result != Validated Result",
        "Business Question",
        "Coverage proposal:",
        "Insufficient evidence to conclude why Revenue declined.",
        "ClaimDecision",
        "MetricState",
        "ClaimState",
    ):
        assert old_english_block not in traditional_chinese


def test_critical_links_exist_in_both_languages() -> None:
    _, english, traditional_chinese = _sections()
    required = {
        "docs/USAGE.md",
        "docs/DEVELOPMENT.md",
        "examples/public_v0_1/README.md",
        "validation/p15/P00_INTERNAL_PROTOCOL_REHEARSAL_CLOSEOUT.md",
        "release-notes/v0.2.0.md",
        "LICENSE",
    }
    for section in (english, traditional_chinese):
        assert required <= set(LINK_RE.findall(section))


def test_all_local_readme_links_and_images_resolve() -> None:
    for target in LINK_RE.findall(_text()):
        if target.startswith(("#", "http://", "https://")):
            continue
        path = target.split("#", 1)[0]
        assert (REPO_ROOT / path).exists(), target


def test_bilingual_flow_assets_are_accessible_valid_svg() -> None:
    text = _text()
    assert FLOW_ASSETS <= set(LINK_RE.findall(text))
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for relative_path in FLOW_ASSETS:
        root = ET.parse(REPO_ROOT / relative_path).getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib.get("role") == "img"
        assert root.attrib.get("aria-labelledby") == "title desc"
        assert root.find("svg:title", namespace) is not None
        assert root.find("svg:desc", namespace) is not None
