import spacy
from spacy.matcher import Matcher, DependencyMatcher
import json

# Try loading the large transformer model first
try:
    nlp = spacy.load("en_core_web_trf")
    print("✅ Loaded transformer model: en_core_web_trf")
except OSError:
    print("⚠️ Transformer model not found. Falling back to en_core_web_sm.")
    nlp = spacy.load("en_core_web_sm")

# Try to add Coreferee only once
try:
    import coreferee
    if "coreferee" not in nlp.pipe_names:
        nlp.add_pipe("coreferee")
        print("✅ Coreferee added successfully.")
    else:
        print("ℹ️ Coreferee already exists in pipeline.")
except Exception as e:
    print(f"⚠️ Coreferee not available or failed to load: {e}")

# Initialize matchers
matcher = Matcher(nlp.vocab)
dep_matcher = DependencyMatcher(nlp.vocab)

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

    # Resolve coreferences if available
    if nlp.has_pipe("coreferee") and hasattr(doc._, "coref_resolved"):
        try:
            resolved_text = doc._.coref_resolved
            doc = nlp(resolved_text)
        except Exception as e:
            print(f"⚠️ Coreference resolution failed: {e}")

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
        if any(tok.lower_ in ["feature", "module", "dashboard", "login", "function"] for tok in chunk):
            ner_map["features"].setdefault(span_text, {"owned_by": [], "depends_on": [], "constraints": [], "satisfied_by": [], "supported_by": [], "validated_by": []})
        if any(tok.pos_ == "PROPN" for tok in chunk):
            ner_map["stakeholders"].setdefault(span_text, {"owns": [], "supports": []})
        if any(tok.lower_ in ["shall", "should", "must", "requirement"] for tok in chunk):
            ner_map["requirements"].setdefault(span_text, {"satisfied_by": [], "refines": [], "validated_by": []})
        if any(tok.lower_ in ["constraint", "limit", "budget", "performance"] for tok in chunk):
            ner_map["constraints"].setdefault(span_text, {"applies_to": []})
        if any(tok.lower_ in ["test", "verify", "validate", "check"] for tok in chunk):
            ner_map["test_cases"].setdefault(span_text, {"validates": []})
        if any(tok.lower_ in ["design", "architecture", "layout", "schema", "frontend", "backend", "api"] for tok in chunk):
            ner_map["design"].setdefault(span_text, {"related_to": []})

    # ---- Extract relationships using DependencyMatcher ----
    dep_matches = dep_matcher(doc)
    for match_id, token_ids in dep_matches:
        rel_type = nlp.vocab.strings[match_id]
        ent1 = doc[token_ids[0]].text
        ent2 = doc[token_ids[2]].text

        if rel_type == "DEPENDS_ON":
            ner_map["features"].get(ent1, {}).get("depends_on", []).append(ent2)
        elif rel_type == "DERIVED_ON":
            ner_map["requirements"].get(ent1, {}).get("refines", []).append(ent2)
        elif rel_type == "OWNED_BY":
            if ent1 in ner_map["features"] and ent2 in ner_map["stakeholders"]:
                ner_map["features"][ent1]["owned_by"].append(ent2)
                ner_map["stakeholders"][ent2]["owns"].append(ent1)
        elif rel_type == "REFINES":
            ner_map["requirements"].get(ent1, {}).get("refines", []).append(ent2)
        elif rel_type == "SATISFIED_BY":
            ner_map["requirements"].get(ent1, {}).get("satisfied_by", []).append(ent2)
        elif rel_type == "SUPPORTED_BY":
            ner_map["features"].get(ent1, {}).get("supported_by", []).append(ent2)
        elif rel_type == "VALIDATED_BY":
            ner_map["requirements"].get(ent1, {}).get("validated_by", []).append(ent2)

    return ner_map
