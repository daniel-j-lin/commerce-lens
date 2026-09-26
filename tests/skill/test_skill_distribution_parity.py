from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SKILL = ROOT / "skills" / "commerce-lens" / "SKILL.md"
RUNTIME_SKILL = ROOT / "src" / "commerce_lens" / "skill" / "SKILL.md"


def test_public_critical_skill_instructions_have_behavioral_parity() -> None:
    documents = {
        "canonical": CANONICAL_SKILL.read_text(encoding="utf-8"),
        "runtime": RUNTIME_SKILL.read_text(encoding="utf-8"),
    }
    required_concepts = (
        "mapping confirmation",
        'confirmation_intent="confirmed"',
        "USER_DECLARED",
        "not been independently verified",
        "data-availability cutoff",
        "proposal fingerprint",
        "retained_complete",
        "temporary",
        "list",
        "inspect",
        "verify",
        "Insufficient evidence to conclude.",
        "weekly_product_presence_revenue_association@1.0.0",
        "fail-closed",
    )

    for role, document in documents.items():
        missing = [concept for concept in required_concepts if concept not in document]
        assert missing == [], f"{role} Skill is missing public-critical concepts: {missing}"
