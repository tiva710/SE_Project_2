# nlp_service.py (hybrid with cleanup + dedupe)

import re
import json
from typing import Dict, List, Tuple, Optional

# -------- Optional punctuation restoration ------------------------------------
try:
    from deepmultilingualpunctuation import PunctuationModel
    _PUNCT = PunctuationModel()
    print("✅ PunctuationModel loaded (nlp_service hybrid).")
except Exception as e:
    _PUNCT = None
    print(f"⚠️ PunctuationModel not available: {e}")

# -------- Punctuation + sentence splitting ------------------------------------

def _restore_punctuation(text: str, force: bool = False) -> str:
    if not text or _PUNCT is None:
        return text
    needs = force or (len(re.findall(r"[.!?]", text)) < 3 and len(text.split()) > 30)
    if needs:
        try:
            print("🛠️ Restoring punctuation (nlp_service)…")
            return _PUNCT.restore_punctuation(text)
        except Exception as e:
            print(f"⚠️ restore_punctuation failed: {e}")
    return text

def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p and p.strip()]

# -------- Text normalization ---------------------------------------------------

def _normalize_text_for_entities(text: str) -> str:
    fixes = [
        (r"\bconstrained\b", "constraint"),
        (r"\bConstrained\b", "Constraint"),
        (r"\bapply\b(?=\s+to\b)", "applies"),
    ]
    for pat, rep in fixes:
        text = re.sub(pat, rep, text)
    return text

def _strip_punct_edges(s: str) -> str:
    return s.strip().strip(".,;:!?\"'()[]{}")

def _strip_leading_articles_verbs(s: str) -> str:
    s = re.sub(r"^(the|a|an)\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^(presented|mentioned|explained|said|stated|is|are|was|were)\s+", "", s, flags=re.IGNORECASE)
    return s.strip()

def _truncate_to_suffix(s: str, suffixes=("feature","module","component","requirements","requirement","constraint","constraints","team")) -> str:
    pattern = r"^(.+?\b(?:%s)\b)" % "|".join(suffixes)
    m = re.search(pattern, s, flags=re.IGNORECASE)
    return m.group(1).strip() if m else s.strip()

def _normalize_entity_name(label: str, name: str) -> str:
    name = _strip_punct_edges(name)
    name = _strip_leading_articles_verbs(name)
    name = _truncate_to_suffix(name)
    if label in ("Requirement","Constraint","Team"):
        name = re.sub(r"^(the|a|an)\s+", "", name, flags=re.IGNORECASE)
    # canonical capitalization: keep original case as provided
    return " ".join(name.split())

def _normalize_id(label: str, name: str) -> str:
    clean = re.sub(r"\s+", "_", name.strip().lower())
    return f"{label.lower()}:{clean}"

# -------- Deterministic entity extraction -------------------------------------

ENTITY_PATTERNS = {
    "Feature": re.compile(r"\b([A-Z][a-zA-Z0-9]*(?:\s[A-Z][a-zA-Z0-9]*)*\s(?:feature|module|component))\b", re.IGNORECASE),
    "Team": re.compile(r"\b([A-Z][a-zA-Z0-9]*(?:\s[A-Z][a-zA-Z0-9]*)*\sTeam)\b"),
    "Requirement": re.compile(r"\b([A-Z][a-zA-Z0-9]*(?:\s[A-Z][a-zA-Z0-9]*)*\s(?:requirement|requirements))\b", re.IGNORECASE),
    "Constraint": re.compile(r"\b([A-Z][a-zA-Z0-9]*(?:\s[A-Z][a-zA-Z0-9]*)*\s(?:constraint|constraints))\b", re.IGNORECASE),
    "TestCase": re.compile(r"\b(TC[- ]?\d+)\b", re.IGNORECASE),
}

def _extract_entities(text: str) -> Tuple[List[Dict], Dict[str, Dict]]:
    text = _normalize_text_for_entities(text)
    entities: List[Dict] = []
    emap: Dict[str, Dict] = {}

    for label, pattern in ENTITY_PATTERNS.items():
        for m in pattern.finditer(text):
            raw = m.group(1).strip()
            name = _normalize_entity_name(label, raw)
            if label == "TestCase":
                name = name.upper().replace(" ", "")
            ent_id = _normalize_id(label, name)
            if ent_id not in emap:
                ent = {"id": ent_id, "label": label, "name": name}
                emap[ent_id] = ent
                entities.append(ent)
    return entities, emap

# -------- Relationship extraction ---------------------------------------------

T_DEPENDS = re.compile(r"\b(depends on|requires|relies on)\b", re.IGNORECASE)
T_OWNED_BY = re.compile(r"\b(is owned by|owned by)\b", re.IGNORECASE)
T_SUPPORTED_BY = re.compile(r"\b(is supported by|supported by)\b", re.IGNORECASE)
T_SATISFIES = re.compile(r"\b(must satisfy|satisfies)\b", re.IGNORECASE)
T_APPLIES = re.compile(r"\b(apply to|applies to|apply|applies)\b", re.IGNORECASE)
T_VALIDATES = re.compile(r"\b(validate|validates|verify|verifies)\b", re.IGNORECASE)
T_IMPLEMENTS = re.compile(r"\b(implements)\b", re.IGNORECASE)
T_REFINES = re.compile(r"\b(refines)\b", re.IGNORECASE)
T_DERIVED_FROM = re.compile(r"\b(is derived from|derived from)\b", re.IGNORECASE)
T_RESPONSIBLE_FOR = re.compile(r"\b(is responsible for|responsible for)\b", re.IGNORECASE)

def _split_on(pattern: re.Pattern, sentence: str) -> Tuple[str, str]:
    parts = pattern.split(sentence, maxsplit=1)
    if len(parts) >= 3:
        left = _strip_punct_edges(parts[0])
        right = _strip_punct_edges(parts[2])
        return left, right
    return sentence, ""

def _split_list(fragment: str) -> List[str]:
    parts = re.split(r"\s*(?:,|\band\b)\s*", fragment, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]

def _ensure_ent(emap: Dict[str, Dict], label: str, name: str) -> Dict:
    name = _normalize_entity_name(label, name)
    ent_id = _normalize_id(label, name)
    if ent_id not in emap:
        emap[ent_id] = {"id": ent_id, "label": label, "name": name}
    return emap[ent_id]

def _pick_many(label: str, fragment: str, rx: re.Pattern, emap: Dict[str, Dict]) -> List[Dict]:
    out = []
    for chunk in _split_list(fragment):
        m = rx.search(chunk)
        if not m:
            continue
        name = m.group(1).strip()
        if label == "TestCase":
            name = name.upper().replace(" ", "")
        out.append(_ensure_ent(emap, label, name))
    return out

def _pick_features(fragment, emap): return _pick_many("Feature", fragment, ENTITY_PATTERNS["Feature"], emap)
def _pick_requirements(fragment, emap): return _pick_many("Requirement", fragment, ENTITY_PATTERNS["Requirement"], emap)
def _pick_constraints(fragment, emap): return _pick_many("Constraint", fragment, ENTITY_PATTERNS["Constraint"], emap)
def _pick_teams(fragment, emap): return _pick_many("Team", fragment, ENTITY_PATTERNS["Team"], emap)
def _pick_tests(fragment, emap): return _pick_many("TestCase", fragment, ENTITY_PATTERNS["TestCase"], emap)

def _fanout_rel(srcs: List[Dict], reltype: str, dsts: List[Dict]) -> List[Dict]:
    rels = []
    for s in srcs:
        for d in dsts:
            rels.append({"source": s["id"], "type": reltype, "target": d["id"]})
    return rels

def _dedupe_relationships(rels: List[Dict]) -> List[Dict]:
    seen, out = set(), []
    for r in rels:
        key = (r["source"], r["type"], r["target"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out

def _extract_relationships(sentences: List[str], emap: Dict[str, Dict]) -> List[Dict]:
    rels: List[Dict] = []
    for sent in sentences:
        if T_DEPENDS.search(sent):
            left, right = _split_on(T_DEPENDS, sent)
            rels += _fanout_rel(_pick_features(left, emap), "DEPENDS_ON", _pick_features(right, emap))

        if T_OWNED_BY.search(sent):
            left, right = _split_on(T_OWNED_BY, sent)
            rels += _fanout_rel(_pick_features(left, emap), "OWNED_BY", _pick_teams(right, emap))

        if T_SUPPORTED_BY.search(sent):
            left, right = _split_on(T_SUPPORTED_BY, sent)
            feats = _pick_features(left, emap)
            teams = _pick_teams(right, emap)
            for f in feats:
                for t in teams:
                    rels.append({"source": f["id"], "type": "SUPPORTED_BY", "target": t["id"]})

        if T_SATISFIES.search(sent):
            left, right = _split_on(T_SATISFIES, sent)
            rels += _fanout_rel(_pick_features(left, emap), "SATISFIES", _pick_requirements(right, emap))

        if T_APPLIES.search(sent):
            left, right = _split_on(T_APPLIES, sent)
            rels += _fanout_rel(_pick_constraints(left, emap), "APPLIES_TO", _pick_features(right, emap))

        if T_VALIDATES.search(sent):
            left, right = _split_on(T_VALIDATES, sent)
            rels += _fanout_rel(_pick_tests(left, emap), "VALIDATES", _pick_features(right, emap))

        if T_IMPLEMENTS.search(sent):
            left, right = _split_on(T_IMPLEMENTS, sent)
            rels += _fanout_rel(_pick_features(left, emap), "IMPLEMENTS", _pick_features(right, emap))

        if T_REFINES.search(sent):
            left, right = _split_on(T_REFINES, sent)
            rels += _fanout_rel(_pick_features(left, emap), "REFINES", _pick_requirements(right, emap))

        if T_DERIVED_FROM.search(sent):
            left, right = _split_on(T_DERIVED_FROM, sent)
            rels += _fanout_rel(_pick_features(left, emap), "DERIVED_FROM", _pick_features(right, emap))

        if T_RESPONSIBLE_FOR.search(sent):
            left, right = _split_on(T_RESPONSIBLE_FOR, sent)
            teams = _pick_teams(left, emap) or _pick_features(left, emap)
            reqs = _pick_requirements(right, emap)
            for t in teams:
                for r in reqs:
                    rels.append({"source": t["id"], "type": "RESPONSIBLE_FOR", "target": r["id"]})

    return _dedupe_relationships(rels)

# -------- Public API for routes ------------------------------------------------

def run_ner_to_neo4j(text: str, always_restore_punct: bool = True) -> Dict:
    """
    Hybrid pipeline:
      1) Restore punctuation for Whisper-like text.
      2) Extract entities via stricter rules with span cleanup.
      3) Extract relationships via expanded templates with coordination.
      4) Dedupe relationships.
    Returns {'entities': [...], 'relationships': [...]}.
    """
    text = _restore_punctuation(text, force=always_restore_punct)
    entities, emap = _extract_entities(text)
    sentences = _split_sentences(text)
    relationships = _extract_relationships(sentences, emap)

    result = {"entities": entities, "relationships": relationships}

    # Optional logging
    try:
        print("\nNEO4J FORMAT OUTPUT (hybrid):")
        print(json.dumps(result, indent=2))
        print("=" * 80)
        print(f"✅ Total Entities: {len(result['entities'])}")
        print(f"✅ Total Relationships: {len(result['relationships'])}")
        print("=" * 80)
    except Exception:
        pass

    return result