import re
import json
import pytest

# Adjust import based on your actual module name:
# If your code is in backend/app/services/nlp_service.py:
from app.services.nlp_service import run_ner_to_neo4j

# If you moved your hybrid code to nlp_service_hybrid.py instead, use:
# from app.services.nlp_service_hybrid import run_ner_to_neo4j


def find_entity(result, label, name=None):
    ents = [e for e in result["entities"] if e["label"] == label]
    if name is not None:
        ents = [e for e in ents if e["name"] == name]
    return ents


def make_id(label: str, name: str) -> str:
    # Build IDs without backslashes inside f-strings
    norm = re.sub(r"\s+", "_", name.lower())
    return f"{label.lower()}:{norm}"


def has_rel(result, source_label, source_name, reltype, target_label, target_name):
    src_id = make_id(source_label, source_name)
    dst_id = make_id(target_label, target_name)
    return any(
        r["source"] == src_id and r["type"] == reltype and r["target"] == dst_id
        for r in result["relationships"]
    )


def test_punctuation_restoration_basic():
    text = "the login feature depends on authentication module it must satisfy security requirements and performance requirements"
    res = run_ner_to_neo4j(text, always_restore_punct=True)
    assert isinstance(res, dict)
    assert "entities" in res and "relationships" in res
    assert len(res["entities"]) >= 1


def test_feature_extraction_and_normalization():
    text = "The Login Feature and Reporting Module were discussed."
    res = run_ner_to_neo4j(text)
    feats = find_entity(res, "Feature")
    names = {e["name"] for e in feats}
    assert "Login Feature" in names
    assert "Reporting Module" in names


def test_requirement_and_constraint_extraction():
    text = "The authentication requirements and API constraints are critical."
    res = run_ner_to_neo4j(text)
    reqs = find_entity(res, "Requirement")
    cons = find_entity(res, "Constraint")
    assert any("authentication requirements" == e["name"] for e in reqs)
    assert any("constraints" in e["name"].lower() for e in cons)


def test_team_and_testcase_extraction():
    text = "Quality Assurance Team will run TC-123 and tc 456."
    res = run_ner_to_neo4j(text)
    teams = find_entity(res, "Team", "Quality Assurance Team")
    tcs = find_entity(res, "TestCase")
    ids = {e["name"] for e in tcs}
    assert len(teams) == 1
    assert "TC-123" in ids
    assert "TC-456" in ids


def test_depends_on_relationship_single():
    text = "Login Feature depends on Authentication Module."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Login Feature", "DEPENDS_ON", "Feature", "Authentication Module")


def test_depends_on_with_and_list():
    text = "Reporting Module depends on Analytics Module and Export Module."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Reporting Module", "DEPENDS_ON", "Feature", "Analytics Module")
    assert has_rel(res, "Feature", "Reporting Module", "DEPENDS_ON", "Feature", "Export Module")


def test_owned_by_relationship():
    text = "Login Feature is owned by Platform Team."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Login Feature", "OWNED_BY", "Team", "Platform Team")


def test_supported_by_relationship():
    text = "Login Feature is supported by Security Team and Reliability Team."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Login Feature", "SUPPORTED_BY", "Team", "Security Team")
    assert has_rel(res, "Feature", "Login Feature", "SUPPORTED_BY", "Team", "Reliability Team")


def test_satisfies_relationship_singular_and_plural():
    text = "Login Feature must satisfy Authentication Requirements and Performance Requirements."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Login Feature", "SATISFIES", "Requirement", "Authentication Requirements")
    assert has_rel(res, "Feature", "Login Feature", "SATISFIES", "Requirement", "Performance Requirements")


def test_applies_to_constraints():
    text = "API Constraints apply to Reporting Module."
    res = run_ner_to_neo4j(text)
    cons = find_entity(res, "Constraint")
    assert len(cons) >= 1
    assert has_rel(res, "Constraint", cons[0]["name"], "APPLIES_TO", "Feature", "Reporting Module")


def test_validates_relationship():
    text = "TC-101 validates Login Feature."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "TestCase", "TC-101", "VALIDATES", "Feature", "Login Feature")


def test_implements_relationship():
    text = "Export Module implements Analytics Module."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Export Module", "IMPLEMENTS", "Feature", "Analytics Module")


def test_refines_relationship():
    text = "Search Module refines Functional Requirements."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Search Module", "REFINES", "Requirement", "Functional Requirements")


def test_derived_from_relationship():
    text = "Invoice Feature is derived from Billing Feature."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Feature", "Invoice Feature", "DERIVED_FROM", "Feature", "Billing Feature")


def test_responsible_for_relationship_team_to_requirement():
    text = "Security Team is responsible for Authentication Requirements."
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Team", "Security Team", "RESPONSIBLE_FOR", "Requirement", "Authentication Requirements")


def test_dedupe_relationships():
    text = "Login Feature depends on Authentication Module. Login Feature depends on Authentication Module."
    res = run_ner_to_neo4j(text)
    deps = [r for r in res["relationships"] if r["type"] == "DEPENDS_ON"]
    assert len(deps) == 1


def test_normalization_edges():
    text = ("The API Constraints applies to the   Login Feature. "
            "The presented Login Feature depends on the Analytics Module.")
    res = run_ner_to_neo4j(text)
    assert has_rel(res, "Constraint", "API Constraints", "APPLIES_TO", "Feature", "Login Feature")
    assert has_rel(res, "Feature", "Login Feature", "DEPENDS_ON", "Feature", "Analytics Module")


def test_no_crash_on_empty_and_minimal_input():
    assert run_ner_to_neo4j("") == {"entities": [], "relationships": []}
    res = run_ner_to_neo4j("Hello world.")
    assert isinstance(res, dict) and "entities" in res and "relationships" in res


def test_json_serializable_output():
    text = "Login Feature depends on Authentication Module."
    res = run_ner_to_neo4j(text)
    payload = json.dumps(res)
    assert isinstance(payload, str)
