import spacy
from spacy.matcher import Matcher, DependencyMatcher
import coreferee  # modern spaCy coref resolver
import json

# Load a supported spaCy model directly
nlp = spacy.load("en_core_web_trf")  # or "en_core_web_sm"

# Add Coreferee after loading the model
nlp.add_pipe('coreferee')

# Add coreference resolver
nlp.add_pipe('coreferee')

matcher = Matcher(nlp.vocab)
dep_matcher = DependencyMatcher(nlp.vocab)
# sample_transcript = """
# Alice, the Product Manager, said that the Login Feature shall allow users to authenticate with their email and password.
# Bob, the Lead Developer, mentioned that this feature depends on the Authentication Module.
# The Authentication Module must satisfy the security requirements and is constrained by the performance limit of 2 seconds per login.
# Charlie, the QA Lead, will validate the Login Feature using Test Case TC-01 and TC-02.
# The Dashboard Feature relies on the Login Feature and should display user-specific information.
# The Reporting Feature is derived from the Dashboard Feature and refines the existing analytics requirements.
# The Login Feature is supported by Alice and the Operations Team.
# All requirements must be validated by the corresponding test cases.
# It should also be owned by Bob.
# """


# -------------------- Helper to add dependency patterns --------------------
def add_dep_pattern(dep_matcher, rel_name, ent1_label, verb_lemmas, ent2_label):
    pattern = [
        {"RIGHT_ID": "ent1", "RIGHT_ATTRS": {"ENT_TYPE": ent1_label}},
        {"REL_OP": ">", "LEFT_ID": "ent1", "RIGHT_ID": "verb", "RIGHT_ATTRS": {"LEMMA": {"IN": verb_lemmas}, "POS": "VERB"}},
        {"REL_OP": ">", "LEFT_ID": "verb", "RIGHT_ID": "ent2", "RIGHT_ATTRS": {"ENT_TYPE": ent2_label}}
    ]
    dep_matcher.add(rel_name, [pattern])

# -------------------- Add all Neo4j relationship patterns --------------------
add_dep_pattern(dep_matcher, "DEPENDS_ON", "FEATURE", ["depend", "require", "rely"], "FEATURE")
add_dep_pattern(dep_matcher, "DERIVED_ON", "REQUIREMENT", ["derive"], "REQUIREMENT")
add_dep_pattern(dep_matcher, "OWNED_BY", "FEATURE", ["own", "belong"], "STAKEHOLDER")
add_dep_pattern(dep_matcher, "REFINES", "REQUIREMENT", ["refine"], "REQUIREMENT")
add_dep_pattern(dep_matcher, "SATISFIED_BY", "REQUIREMENT", ["satisfy"], "FEATURE")
add_dep_pattern(dep_matcher, "SUPPORTED_BY", "FEATURE", ["support"], "STAKEHOLDER")
add_dep_pattern(dep_matcher, "VALIDATED_BY", "REQUIREMENT", ["validate", "verify", "check"], "TESTCASE")

# -------------------- Main NER + RE with Coref --------------------
def process_conversation(text: str):
    doc = nlp(text)
    
    # Resolve coreferences
    resolved_text = doc._.coref_resolved
    doc = nlp(resolved_text)  # re-parse resolved text

    ner_map = {
        "features": {},
        "stakeholders": {},
        "requirements": {},
        "constraints": {},
        "test_cases": {},
        "design": {}
    }

    # ---- Dynamically detect entities ----
    for chunk in doc.noun_chunks:
        span_text = chunk.text.strip()
        # Features
        if any(tok.lower_ in ["feature", "module", "dashboard", "login", "function"] for tok in chunk):
            if span_text not in ner_map["features"]:
                ner_map["features"][span_text] = {
                    "owned_by": [], "depends_on": [], "constraints": [], 
                    "satisfied_by": [], "supported_by": [], "validated_by": []
                }
        # Stakeholders (proper nouns)
        if any(tok.pos_ == "PROPN" for tok in chunk):
            if span_text not in ner_map["stakeholders"]:
                ner_map["stakeholders"][span_text] = {"owns": [], "supports": []}
        # Requirements
        if any(tok.lower_ in ["shall", "should", "must", "requirement"] for tok in chunk):
            if span_text not in ner_map["requirements"]:
                ner_map["requirements"][span_text] = {"satisfied_by": [], "refines": [], "validated_by": []}
        # Constraints
        if any(tok.lower_ in ["constraint", "limit", "budget", "performance"] for tok in chunk):
            if span_text not in ner_map["constraints"]:
                ner_map["constraints"][span_text] = {"applies_to": []}
        # TestCases
        if any(tok.lower_ in ["test", "verify", "validate", "check"] for tok in chunk):
            if span_text not in ner_map["test_cases"]:
                ner_map["test_cases"][span_text] = {"validates": []}
        # Design
        if any(tok.lower_ in ["design", "architecture", "layout", "schema", "frontend", "backend", "api"] for tok in chunk):
            if span_text not in ner_map["design"]:
                ner_map["design"][span_text] = {"related_to": []}

    # ---- Extract relationships using DependencyMatcher ----
    dep_matches = dep_matcher(doc)
    for match_id, token_ids in dep_matches:
        rel_type = nlp.vocab.strings[match_id]
        ent1 = doc[token_ids[0]].text
        ent2 = doc[token_ids[2]].text

        if rel_type == "DEPENDS_ON" and ent1 in ner_map["features"] and ent2 in ner_map["features"]:
            ner_map["features"][ent1]["depends_on"].append(ent2)
        elif rel_type == "DERIVED_ON" and ent1 in ner_map["requirements"] and ent2 in ner_map["requirements"]:
            ner_map["requirements"][ent1]["refines"].append(ent2)
        elif rel_type == "OWNED_BY" and ent1 in ner_map["features"] and ent2 in ner_map["stakeholders"]:
            ner_map["features"][ent1]["owned_by"].append(ent2)
            ner_map["stakeholders"][ent2]["owns"].append(ent1)
        elif rel_type == "REFINES" and ent1 in ner_map["requirements"] and ent2 in ner_map["requirements"]:
            ner_map["requirements"][ent1]["refines"].append(ent2)
        elif rel_type == "SATISFIED_BY" and ent1 in ner_map["requirements"] and ent2 in ner_map["features"]:
            ner_map["requirements"][ent1]["satisfied_by"].append(ent2)
            ner_map["features"][ent2]["satisfied_by"].append(ent1)
        elif rel_type == "SUPPORTED_BY" and ent1 in ner_map["features"] and ent2 in ner_map["stakeholders"]:
            ner_map["features"][ent1]["supported_by"].append(ent2)
            ner_map["stakeholders"][ent2]["supports"].append(ent1)
        elif rel_type == "VALIDATED_BY" and ent1 in ner_map["requirements"] and ent2 in ner_map["test_cases"]:
            ner_map["requirements"][ent1]["validated_by"].append(ent2)
            ner_map["test_cases"][ent2]["validates"].append(ent1)

    return ner_map


# result = process_conversation(sample_transcript)
# print(result)