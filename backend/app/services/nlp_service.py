import spacy
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import json
from spacy.matcher import Matcher, DependencyMatcher
from collections import defaultdict


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
    

@dataclass
class Entity:
    """Base class for all extracted entities"""
    id: str
    text: str
    type: str
    context: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def to_neo4j_node(self):
        """Convert to Neo4j node format"""
        return {
            'id': self.id,
            'label': self.type,
            'properties': {
                'name': self.text,
                'context': self.context,
                **self.metadata
            }
        }


@dataclass
class Feature(Entity):
    owned_by: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    derives_from: List[str] = field(default_factory=list)
    refines: List[str] = field(default_factory=list)
    satisfied_by: List[str] = field(default_factory=list)
    supported_by: List[str] = field(default_factory=list)
    validated_by: List[str] = field(default_factory=list)
    relies_on: List[str] = field(default_factory=list)


@dataclass
class Requirement(Entity):
    satisfied_by: List[str] = field(default_factory=list)
    owned_by: List[str] = field(default_factory=list)
    validated_by: List[str] = field(default_factory=list)
    refined_by: List[str] = field(default_factory=list)


@dataclass
class TestCase(Entity):
    validates: List[str] = field(default_factory=list)
    owned_by: List[str] = field(default_factory=list)


@dataclass
class Stakeholder(Entity):
    role: str = ""
    owns: List[str] = field(default_factory=list)
    supports: List[str] = field(default_factory=list)
    
    def to_neo4j_node(self):
        """Override to include role"""
        return {
            'id': self.id,
            'label': self.type,
            'properties': {
                'name': self.text,
                'role': self.role,
                'context': self.context,
                **self.metadata
            }
        }


@dataclass
class Constraint(Entity):
    applies_to: List[str] = field(default_factory=list)


@dataclass
class Design(Entity):
    implements: List[str] = field(default_factory=list)
    satisfies: List[str] = field(default_factory=list)


class RequirementsNERToNeo4j:
    """NER for extracting requirements entities and converting to Neo4j format"""
    
    def __init__(self, use_spacy: bool = True):
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                print("Warning: spaCy not available. Using regex-only mode.")
                self.use_spacy = False
        
        # Entity extraction patterns - FIXED to handle hyphenated names
        self.feature_patterns = [
            r'\b(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component|Functionality))\b',
            r'\b(F-\d+)\b',
        ]
        
        # FIXED: More flexible requirement pattern
        self.requirement_patterns = [
            r'\b([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)\b',
            r'\b(R-\d+)\b',
        ]
        
        self.test_patterns = [
            r'\b(?:Test Case\s+)?(TC-\d+)\b',
            r'\b(T-\d+)\b',
        ]
        
        self.constraint_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Constraint)\b',
            r'\b(C-\d+)\b',
        ]
        
        self.design_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Design|Architecture))\b',
            r'\b(D-\d+)\b',
        ]
        
        # Relationship extraction patterns
        self.relationship_patterns = {
            'owned_by': r'(?:owned by|assigned to|belongs to)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+Team)?)',
            'depends_on': r'(?:depends on|dependent on|requires)\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component)|[A-Z]-\d+)',
            'relies_on': r'(?:relies on|reliant on|based on)\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component)|[A-Z]-\d+)',
            'derives_from': r'(?:derived from|derives from)\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component)|[A-Z]-\d+)',
            'refines': r'refines\s+(?:the\s+)?(?:existing\s+)?([a-z]+(?:\s+[a-z]+)*\s+requirements?)',
            'satisfied_by': r'(?:satisfied by|implemented by|met by)\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module)|[A-Z]-\d+)',
            'must_satisfy': r'must satisfy\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+)*\s+requirements?)',
            'supported_by': r'(?:supported by|backed by)\s+([A-Z][a-z]+(?:\s+(?:and\s+)?(?:the\s+)?[A-Z][a-z]+)*(?:\s+Team)?)',
            'validated_by': r'(?:validate|validated by|verify|verified by)\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component))\s+using\s+(.+?)(?:\.|$)',
            'validates': r'(?:validate|validates|verify|verifies)\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component)|[A-Z]-\d+)',
            'applies_to': r'(?:applies to|constrains)\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component|System)|[A-Z]-\d+)',
            'implements': r'implements\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component)|[A-Z]-\d+)',
        }
    
    def process_text(self, text: str) -> Dict:
        """
        Main public method to process text and return Neo4j format.
        This is the method that should be called from other services.
        
        Args:
            text (str): The input text containing requirements, features, etc.
            
        Returns:
            Dict: Neo4j formatted data with 'entities' and 'relationships' keys
        """
        entities, entity_map = self.extract_entities(text)
        neo4j_data = self.convert_to_neo4j_format(entities, entity_map)
        return neo4j_data
    
    def extract_entities(self, text: str) -> Tuple[Dict[str, List[Entity]], Dict]:
        """Extract entities from text"""
        entities = {
            'features': [],
            'requirements': [],
            'tests': [],
            'stakeholders': [],
            'constraints': [],
            'designs': []
        }
        
        entity_map = {}
        
        # Extract stakeholders first
        stakeholders = self._extract_stakeholders(text)
        for s in stakeholders:
            entities['stakeholders'].append(s)
            entity_map[s.text.lower()] = s
        
        # Extract features
        for pattern in self.feature_patterns:
            for match in re.finditer(pattern, text):
                feature_text = match.group(1).strip()
                feature_text = re.sub(r'^[Tt]he\s+', '', feature_text)
                normalized = feature_text.lower()
                
                if normalized not in entity_map:
                    feature = Feature(
                        id=self._generate_id('feature', feature_text),
                        text=feature_text,
                        type='Feature',
                        context=self._get_sentence_context(text, match.start())
                    )
                    entities['features'].append(feature)
                    entity_map[normalized] = feature
        
        # Extract requirements - COMPLETELY REWRITTEN
        requirement_in_context_patterns = [
            r'satisfy\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)(?:\s+and\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?))?',  
            r'refines\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)',  
            r'for\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)',
            r'satisfies\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)',
        ]

        for pattern in requirement_in_context_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Handle both group 1 and potentially group 2 (for "and" cases)
                for group_idx in [1, 2]:
                    if match.lastindex >= group_idx and match.group(group_idx):
                        req_text = match.group(group_idx).strip()
                        
                        # Skip if it starts with "and" or "feature"
                        if req_text.lower().startswith(('and ', 'feature ', 'the feature')):
                            continue
                            
                        normalized = req_text.lower()
                        
                        if normalized not in entity_map:
                            requirement = Requirement(
                                id=self._generate_id('requirement', req_text),
                                text=req_text,
                                type='Requirement',
                                context=self._get_sentence_context(text, match.start())
                            )
                            entities['requirements'].append(requirement)
                            entity_map[normalized] = requirement

        
        # Extract test cases
        for pattern in self.test_patterns:
            for match in re.finditer(pattern, text):
                test_text = match.group(1).strip()
                normalized = test_text.lower()
                
                if normalized not in entity_map:
                    test = TestCase(
                        id=self._generate_id('test', test_text),
                        text=test_text,
                        type='TestCase',
                        context=self._get_sentence_context(text, match.start())
                    )
                    entities['tests'].append(test)
                    entity_map[normalized] = test
        
        # Extract constraints
        for pattern in self.constraint_patterns:
            for match in re.finditer(pattern, text):
                constraint_text = match.group(1).strip()
                
                # Check if there's another constraint before this one with "and"
                before_pos = max(0, match.start() - 50)
                before_text = text[before_pos:match.start()]
                
                # Look for "X Constraint and" pattern before current match
                prev_constraint_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Constraint)\s+and\s+(?:the\s+)?$'
                prev_match = re.search(prev_constraint_pattern, before_text)
                if prev_match:
                    prev_constraint_text = prev_match.group(1).strip()
                    prev_constraint_text = re.sub(r'^(?:The|API)\s+', '', prev_constraint_text)
                    prev_normalized = prev_constraint_text.lower()
                    
                    if prev_normalized not in entity_map:
                        prev_constraint = Constraint(
                            id=self._generate_id('constraint', prev_constraint_text),
                            text=prev_constraint_text,
                            type='Constraint',
                            context=self._get_sentence_context(text, before_pos + prev_match.start())
                        )
                        entities['constraints'].append(prev_constraint)
                        entity_map[prev_normalized] = prev_constraint
                
                # Remove "The" or "API" prefix if present
                constraint_text = re.sub(r'^(?:The|API)\s+', '', constraint_text)
                
                normalized = constraint_text.lower()
                
                if normalized not in entity_map:
                    constraint = Constraint(
                        id=self._generate_id('constraint', constraint_text),
                        text=constraint_text,
                        type='Constraint',
                        context=self._get_sentence_context(text, match.start())
                    )
                    entities['constraints'].append(constraint)
                    entity_map[normalized] = constraint

        
        # Extract designs
        for pattern in self.design_patterns:
            for match in re.finditer(pattern, text):
                design_text = match.group(1).strip()
                design_text = re.sub(r'^[Tt]he\s+', '', design_text)
                normalized = design_text.lower()
                
                if normalized not in entity_map:
                    design = Design(
                        id=self._generate_id('design', design_text),
                        text=design_text,
                        type='Design',
                        context=self._get_sentence_context(text, match.start())
                    )
                    entities['designs'].append(design)
                    entity_map[normalized] = design
        
        # Extract relationships
        self._extract_relationships(text, entities, entity_map)
        
        return entities, entity_map
    
    def _extract_stakeholders(self, text: str) -> List[Stakeholder]:
        """Extract stakeholders (people and teams)"""
        stakeholders = []
        seen = set()
        
        if self.nlp:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    # Skip "Test Case" which is not a person
                    if name.lower() in ['test case', 'test']:
                        continue
                    if name not in seen and len(name) > 1:
                        seen.add(name)
                        role = self._find_role_near_name(text, name)
                        
                        stakeholder = Stakeholder(
                            id=self._generate_id('stakeholder', name),
                            text=name,
                            type='Stakeholder',
                            role=role,
                            context=self._get_context(text, name)
                        )
                        stakeholders.append(stakeholder)
        
        # Extract teams
        team_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Team)\b'
        for match in re.finditer(team_pattern, text):
            team_name = match.group(1)
            if team_name not in seen:
                seen.add(team_name)
                stakeholder = Stakeholder(
                    id=self._generate_id('stakeholder', team_name),
                    text=team_name,
                    type='Stakeholder',
                    role='Team',
                    context=self._get_sentence_context(text, match.start())
                )
                stakeholders.append(stakeholder)
        
        # Extract role-based stakeholders (like "Product Manager", "QA Lead")
        role_pattern = r'\b(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+Manager|\s+Lead|\s+Engineer|\s+Analyst|\s+Designer|\s+Architect|\s+Developer|\s+Officer))\b'
        for match in re.finditer(role_pattern, text):
            role_name = match.group(1).strip()
            role_name = re.sub(r'^the\s+', '', role_name, flags=re.IGNORECASE)
            
            # Check if this is part of a person's name
            before_text = text[max(0, match.start()-20):match.start()]
            if not re.search(r'[A-Z][a-z]+,?\s*$', before_text):
                if role_name not in seen:
                    seen.add(role_name)
                    stakeholder = Stakeholder(
                        id=self._generate_id('stakeholder', role_name),
                        text=role_name,
                        type='Stakeholder',
                        role=role_name,
                        context=self._get_sentence_context(text, match.start())
                    )
                    stakeholders.append(stakeholder)
        
        return stakeholders
    
    def _find_role_near_name(self, text: str, name: str) -> str:
        """Find role/title near a person's name"""
        pattern = rf'{re.escape(name)},?\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        match = re.search(pattern, text)
        if match:
            potential_role = match.group(1)
            # Make sure it's not a Feature/Module/System/Component name
            if not re.search(r'(Feature|Module|System|Component)', potential_role):
                return potential_role
        return ""
    
    def _extract_relationships(self, text: str, entities: Dict, entity_map: Dict):
        """Extract relationships between entities"""
        
        def find_entity(text_key: str):
            text_key = text_key.lower().strip()
            # Try exact match
            if text_key in entity_map:
                return entity_map[text_key]
            # Try without "the"
            text_key_no_the = re.sub(r'^the\s+', '', text_key)
            if text_key_no_the in entity_map:
                return entity_map[text_key_no_the]
            # Try without "API"
            text_key_no_api = re.sub(r'^api\s+', '', text_key)
            if text_key_no_api in entity_map:
                return entity_map[text_key_no_api]
            return None
        
        last_feature = None
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Update last_feature if mentioned
            for feat_text, feat_entity in entity_map.items():
                if isinstance(feat_entity, Feature) and feat_entity.text.lower() in sentence.lower():
                    last_feature = feat_entity
                    break
            
            # Extract "must satisfy" relationships - IMPROVED
            must_satisfy_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+must satisfy\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)(?:\s+and\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?))?'
            for match in re.finditer(must_satisfy_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                req_text_1 = match.group(2).strip()
                req_text_2 = match.group(3).strip() if match.group(3) else None
                
                subject_entity = find_entity(subject_text)
                
                if subject_entity and hasattr(subject_entity, 'satisfied_by'):
                    for req_text in [req_text_1, req_text_2]:
                        if req_text:
                            target = find_entity(req_text)
                            if target and target.text not in subject_entity.satisfied_by:
                                subject_entity.satisfied_by.append(target.text)
            
            # Extract "is satisfied by" relationships
            is_satisfied_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+is satisfied by\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))'
            for match in re.finditer(is_satisfied_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                target_text = match.group(2).strip()
                
                subject_entity = find_entity(subject_text)
                target_entity = find_entity(target_text)
                
                if subject_entity and target_entity and hasattr(subject_entity, 'satisfied_by'):
                    if target_entity.text not in subject_entity.satisfied_by:
                        subject_entity.satisfied_by.append(target_entity.text)
            
            # Extract "depends on" relationships with "and"
            depends_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+depends on\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))(?:\s+and\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component)))?'
            for match in re.finditer(depends_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                dep_text_1 = match.group(2).strip()
                dep_text_2 = match.group(3).strip() if match.group(3) else None
                
                subject_entity = find_entity(subject_text)
                
                if subject_entity and hasattr(subject_entity, 'depends_on'):
                    for dep_text in [dep_text_1, dep_text_2]:
                        if dep_text:
                            target = find_entity(dep_text)
                            if target and target.text not in subject_entity.depends_on:
                                subject_entity.depends_on.append(target.text)
            
            # Extract "relies on" relationships with "and"
            relies_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+relies on\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))(?:\s+and\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component)))?'
            for match in re.finditer(relies_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                rel_text_1 = match.group(2).strip()
                rel_text_2 = match.group(3).strip() if match.group(3) else None
                
                subject_entity = find_entity(subject_text)
                
                if subject_entity and hasattr(subject_entity, 'relies_on'):
                    for rel_text in [rel_text_1, rel_text_2]:
                        if rel_text:
                            target = find_entity(rel_text)
                            if target and target.text not in subject_entity.relies_on:
                                subject_entity.relies_on.append(target.text)
            
            # Extract "is derived from" / "derived from" relationships
            derived_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+is derived from\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))'
            for match in re.finditer(derived_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                target_text = match.group(2).strip()
                
                subject_entity = find_entity(subject_text)
                target_entity = find_entity(target_text)
                
                if subject_entity and target_entity and hasattr(subject_entity, 'derives_from'):
                    if target_entity.text not in subject_entity.derives_from:
                        subject_entity.derives_from.append(target_entity.text)
            
            # Extract "refines" relationships
            refines_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+refines\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)'
            for match in re.finditer(refines_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                req_text = match.group(2).strip()
                
                subject_entity = find_entity(subject_text)
                target_entity = find_entity(req_text)
                
                if subject_entity and target_entity and hasattr(subject_entity, 'refines'):
                    if target_entity.text not in subject_entity.refines:
                        subject_entity.refines.append(target_entity.text)
            
            # Extract "owned by" or "is owned by" relationships
            owned_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+is owned by\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+Team)?)'
            for match in re.finditer(owned_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                owner_text = match.group(2).strip()
                
                subject_entity = find_entity(subject_text)
                owner_entity = find_entity(owner_text)
                
                if subject_entity and hasattr(subject_entity, 'owned_by'):
                    if owner_entity:
                        if owner_entity.text not in subject_entity.owned_by:
                            subject_entity.owned_by.append(owner_entity.text)
                    else:
                        if owner_text not in subject_entity.owned_by:
                            subject_entity.owned_by.append(owner_text)
            
            # Extract "supported by" relationships - IMPROVED for multiple supporters
            supported_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|System|Component))\s+(?:is\s+)?supported by\s+(.+?)(?:\.|$)'
            for match in re.finditer(supported_pattern, sentence, re.IGNORECASE):
                subject_text = match.group(1).strip()
                supporters_text = match.group(2).strip()
                
                subject_entity = find_entity(subject_text)
                
                if subject_entity and hasattr(subject_entity, 'supported_by'):
                    # Split by "and" while preserving "the"
                    supporter_parts = re.split(r'\s+and\s+', supporters_text, flags=re.IGNORECASE)
                    for supporter in supporter_parts:
                        supporter = supporter.strip()
                        # Remove "the" prefix
                        supporter = re.sub(r'^the\s+', '', supporter, flags=re.IGNORECASE)
                        if supporter and supporter not in subject_entity.supported_by:
                            subject_entity.supported_by.append(supporter)
            
            # Extract "applies to" (constraints) - Handle multiple constraints with "and"
            applies_pattern = r'(?:the\s+)?(?:API\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Constraint)(?:\s+and\s+(?:the\s+)?(?:API\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Constraint))?\s+apply to\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component|System))'
            for match in re.finditer(applies_pattern, sentence, re.IGNORECASE):
                constraint_text_1 = match.group(1).strip()
                constraint_text_1 = re.sub(r'^(?:The|API)\s+', '', constraint_text_1)
                
                constraint_text_2 = match.group(2).strip() if match.group(2) else None
                if constraint_text_2:
                    constraint_text_2 = re.sub(r'^(?:The|API)\s+', '', constraint_text_2)
                
                target_text = match.group(3).strip()
                target_entity = find_entity(target_text)
                
                for constraint_text in [constraint_text_1, constraint_text_2]:
                    if constraint_text:
                        constraint_entity = find_entity(constraint_text)
                        if constraint_entity and target_entity and hasattr(constraint_entity, 'applies_to'):
                            if target_entity.text not in constraint_entity.applies_to:
                                constraint_entity.applies_to.append(target_entity.text)
            
            # Extract "implements" (designs) - Handle multiple implementations with "and"
            implements_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Design|Architecture))\s+implements\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component))(?:\s+and\s+satisfies\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?))?'
            for match in re.finditer(implements_pattern, sentence, re.IGNORECASE):
                design_text = match.group(1).strip()
                feature_text = match.group(2).strip()
                req_text = match.group(3).strip() if match.group(3) else None
                
                design_entity = find_entity(design_text)
                feature_entity = find_entity(feature_text)
                
                if design_entity and feature_entity and hasattr(design_entity, 'implements'):
                    if feature_entity.text not in design_entity.implements:
                        design_entity.implements.append(feature_entity.text)
                
                # Handle "satisfies" in same sentence
                if req_text and design_entity:
                    req_entity = find_entity(req_text)
                    if req_entity and hasattr(design_entity, 'satisfies'):
                        if req_entity.text not in design_entity.satisfies:
                            design_entity.satisfies.append(req_entity.text)
            
            # Extract "satisfies" (designs satisfying requirements) - standalone
            design_satisfies_pattern = r'(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Design|Architecture))\s+satisfies\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,3}\s+requirements?)'
            for match in re.finditer(design_satisfies_pattern, sentence, re.IGNORECASE):
                design_text = match.group(1).strip()
                req_text = match.group(2).strip()
                
                design_entity = find_entity(design_text)
                req_entity = find_entity(req_text)
                
                if design_entity and req_entity and hasattr(design_entity, 'satisfies'):
                    if req_entity.text not in design_entity.satisfies:
                        design_entity.satisfies.append(req_entity.text)
            
            # Extract "validates" relationships - Single test case
            validates_pattern_single = r'Test Case\s+(T-\d+|TC-\d+)\s+validates?\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component))'
            for match in re.finditer(validates_pattern_single, sentence, re.IGNORECASE):
                test_id = match.group(1).strip()
                feature_name = match.group(2).strip()
                
                test_entity = find_entity(test_id)
                feature_entity = find_entity(feature_name)
                
                if test_entity and feature_entity:
                    if hasattr(test_entity, 'validates'):
                        if feature_entity.text not in test_entity.validates:
                            test_entity.validates.append(feature_entity.text)
                    if hasattr(feature_entity, 'validated_by'):
                        if test_entity.text not in feature_entity.validated_by:
                            feature_entity.validated_by.append(test_entity.text)
            
            # Extract "validates" relationships - Multiple test cases
            validates_pattern_multiple = r'Test Case\s+(TC-\d+)(?:,\s*Test Case\s+(TC-\d+))?(?:,?\s*and\s*Test Case\s+(TC-\d+))?\s+validate\s+(?:the\s+)?([A-Z][a-z]+(?:(?:\s+|-)[A-Z][a-z]+)*\s+(?:Feature|Module|Component))'
            for match in re.finditer(validates_pattern_multiple, sentence, re.IGNORECASE):
                # Extract all test case IDs from the match groups
                test_ids = [match.group(i) for i in range(1, 4) if match.group(i)]
                feature_name = match.group(4).strip()
                
                feature_entity = find_entity(feature_name)
                if feature_entity:
                    for test_id in test_ids:
                        test_entity = find_entity(test_id)
                        if test_entity and hasattr(test_entity, 'validates'):
                            if feature_entity.text not in test_entity.validates:
                                test_entity.validates.append(feature_entity.text)
                        if hasattr(feature_entity, 'validated_by') and test_entity:
                            if test_entity.text not in feature_entity.validated_by:
                                feature_entity.validated_by.append(test_entity.text)
    
    def _get_sentence_context(self, text: str, position: int) -> str:
        """Get the sentence containing the position"""
        before = text[:position]
        after = text[position:]
        
        start = max(before.rfind('.'), before.rfind('!'), before.rfind('?'))
        end = after.find('.')
        
        if end == -1:
            end = len(after)
        if start == -1:
            start = 0
        else:
            start += 1
        
        sentence = text[start:position + end].strip()
        return sentence
    
    def _get_context(self, text: str, entity_text: str, window: int = 100) -> str:
        """Get surrounding context for an entity"""
        pos = text.find(entity_text)
        if pos == -1:
            return ""
        start = max(0, pos - window)
        end = min(len(text), pos + len(entity_text) + window)
        return text[start:end].strip()
    
    def _generate_id(self, entity_type: str, text: str) -> str:
        """Generate unique ID for entity"""
        # Check if text already contains an ID pattern like TC-101, R-5, etc.
        id_match = re.search(r'\b([A-Z]+-\d+)\b', text)
        if id_match:
            base_id = id_match.group(1).lower()
            # Add prefix for test cases
            if entity_type == 'test':
                return f"test.{base_id}"
            return base_id
        
        # Generate ID based on entity type and text
        prefix_map = {
            'feature': 'feature',
            'requirement': 'req',
            'test': 'test',
            'stakeholder': 'stakeholder',
            'constraint': 'constraint',
            'design': 'design'
        }
        
        prefix = prefix_map.get(entity_type, 'entity')
        
        # Clean the text to create a readable ID
        clean_text = text.lower()
        
        # Remove "the", "a", "an" from the beginning
        clean_text = re.sub(r'^\s*(?:the|a|an)\s+', '', clean_text)
        
        # For requirements, keep more context
        if entity_type == 'requirement':
            # Split on "requirements" and keep the descriptive part
            parts = clean_text.split('requirements')
            if len(parts) > 1:
                clean_text = parts[0].strip() + '.requirements'
            else:
                clean_text = clean_text.strip()
        
        # Remove special characters and convert spaces/hyphens to dots
        clean_text = re.sub(r'[^\w\s-]', '', clean_text)
        clean_text = re.sub(r'[\s-]+', '.', clean_text.strip())
        
        # Limit length
        clean_text = clean_text[:50]
        
        return f"{prefix}.{clean_text}"
    
    def convert_to_neo4j_format(self, entities: Dict[str, List[Entity]], entity_map: Dict) -> Dict:
        """Convert extracted entities to Neo4j format"""
        neo4j_entities = []
        neo4j_relationships = []
        
        # Convert all entities to nodes
        all_entities = []
        for entity_list in entities.values():
            all_entities.extend(entity_list)
        
        for entity in all_entities:
            neo4j_entities.append(entity.to_neo4j_node())
        
        # Convert relationships
        for entity in all_entities:
            # Handle Features
            if isinstance(entity, Feature):
                for target_text in entity.owned_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': target.id,
                            'target': entity.id,
                            'type': 'OWNS',
                            'properties': {}
                        })
                
                for target_text in entity.depends_on:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'DEPENDS_ON',
                            'properties': {}
                        })
                
                for target_text in entity.relies_on:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'RELIES_ON',
                            'properties': {}
                        })
                
                for target_text in entity.derives_from:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'DERIVES_FROM',
                            'properties': {}
                        })
                
                for target_text in entity.refines:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'REFINES',
                            'properties': {}
                        })
                
                for target_text in entity.satisfied_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'SATISFIED_BY',
                            'properties': {}
                        })
                
                for target_text in entity.supported_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': target.id,
                            'target': entity.id,
                            'type': 'SUPPORTS',
                            'properties': {}
                        })
                
                for target_text in entity.validated_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': target.id,
                            'target': entity.id,
                            'type': 'VALIDATES',
                            'properties': {}
                        })
            
            # Handle Requirements
            elif isinstance(entity, Requirement):
                for target_text in entity.satisfied_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'SATISFIED_BY',
                            'properties': {}
                        })
                
                for target_text in entity.owned_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': target.id,
                            'target': entity.id,
                            'type': 'OWNS',
                            'properties': {}
                        })
                
                for target_text in entity.validated_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': target.id,
                            'target': entity.id,
                            'type': 'VALIDATES',
                            'properties': {}
                        })
                
                for target_text in entity.refined_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': target.id,
                            'target': entity.id,
                            'type': 'REFINES',
                            'properties': {}
                        })
            
            # Handle TestCases
            elif isinstance(entity, TestCase):
                for target_text in entity.validates:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'VALIDATES',
                            'properties': {}
                        })
                
                for target_text in entity.owned_by:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': target.id,
                            'target': entity.id,
                            'type': 'OWNS',
                            'properties': {}
                        })
            
            # Handle Constraints
            elif isinstance(entity, Constraint):
                for target_text in entity.applies_to:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'APPLIES_TO',
                            'properties': {}
                        })
            
            # Handle Designs
            elif isinstance(entity, Design):
                for target_text in entity.implements:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'IMPLEMENTS',
                            'properties': {}
                        })
                
                for target_text in entity.satisfies:
                    target = self._find_entity_by_text(target_text, entity_map)
                    if target:
                        neo4j_relationships.append({
                            'source': entity.id,
                            'target': target.id,
                            'type': 'SATISFIES',
                            'properties': {}
                        })
        
        return {
            'entities': neo4j_entities,
            'relationships': neo4j_relationships
        }
    
    def _find_entity_by_text(self, text: str, entity_map: Dict) -> Optional[Entity]:
        """Find entity by text in entity map"""
        text_lower = text.lower().strip()
        if text_lower in entity_map:
            return entity_map[text_lower]
        
        # Try without "the"
        text_no_the = re.sub(r'^the\s+', '', text_lower)
        if text_no_the in entity_map:
            return entity_map[text_no_the]
        
        return None


# Example usage showing how to call from another service
if __name__ == "__main__":
    # This is just for testing - remove or comment out in production
    text = """
    Sarah Kim, the Blockchain Lead, presented the Smart Contract Verification Feature during the kickoff meeting.

The Smart Contract Verification Feature must satisfy the security requirements and the compliance requirements.

Robert Davis, the Backend Engineer, mentioned that the Smart Contract Verification Feature depends on the Ethereum Integration Module and the Cryptographic Validation System.

The Transaction Audit Component is derived from the Cryptographic Validation System.

Patricia Lee, the Compliance Manager, explained that the GDPR Constraint and the Financial Regulation Constraint apply to the Smart Contract Verification Feature and the Transaction Audit Component.

The Supply Chain Tracking Module relies on the Smart Contract Verification Feature.

The Smart Contract Verification Feature is owned by the Blockchain Team and supported by Sarah Kim and the Security Team.

Test Case TC-2001 and Test Case TC-2002 validate the Ethereum Integration Module.

The Distributed Ledger Architecture Design implements the Smart Contract Verification Feature and satisfies the immutability requirements.

Test Case T-2003 validates the Transaction Audit Component.

The Supply Chain Tracking Module refines the traceability requirements.

Daniel Foster, the DevOps Engineer, is responsible for the deployment requirements.

The Cryptographic Validation System is owned by the Security Team.


    """
    
    # Initialize NER
    ner = RequirementsNERToNeo4j(use_spacy=True)
    
    # Process text - THIS IS THE METHOD TO CALL FROM OTHER SERVICES
    result = ner.process_text(text)
    
    # Print results
    print("=== NEO4J FORMAT OUTPUT ===\n")
    print(json.dumps(result, indent=2))
    
    print(f"\n\nTotal entities: {len(result['entities'])}")
    print(f"Total relationships: {len(result['relationships'])}")
=======
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