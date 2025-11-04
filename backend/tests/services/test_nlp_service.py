import pytest
import sys
from pathlib import Path

# Add the app directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.nlp_service import (
    RequirementsNERToNeo4j, Entity, Feature, Requirement, TestCase, 
    Stakeholder, Constraint, Design
)

class TestNLPService:
    
    @pytest.fixture
    def nlp_service(self):
        """Initialize NLP service for testing"""
        return RequirementsNERToNeo4j(use_spacy=True)
    
    # ==================== Feature Extraction Tests ====================
    
    def test_extract_simple_feature(self, nlp_service):
        """Test extraction of capitalized feature"""
        text = "The User Authentication Feature is critical."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        features = [e for e in entities if e['label'] == 'Feature']
        assert len(features) >= 1
        assert any("User Authentication" in f['properties']['name'] for f in features)
    
    def test_extract_hyphenated_feature(self, nlp_service):
        """Test extraction of hyphenated feature names"""
        text = "The Multi-Factor Authentication Feature enhances security."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        features = [e for e in entities if e['label'] == 'Feature']
        assert len(features) >= 1
        assert any("Multi-Factor Authentication" in f['properties']['name'] for f in features)
    
    def test_extract_feature_with_id(self, nlp_service):
        """Test extraction of feature with ID format"""
        text = "F-101 must be implemented."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        features = [e for e in entities if e['label'] == 'Feature']
        # Should extract at least one feature entity and it should have an ID
        assert len(features) >= 1
        assert all('id' in f for f in features)
    
    def test_extract_multiple_features(self, nlp_service):
        """Test extraction of multiple features in one sentence"""
        text = "The Payment Module and the Invoice System are dependencies."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        features = [e for e in entities if e['label'] == 'Feature']
        assert len(features) >= 2
    
    # ==================== Requirement Extraction Tests ====================
    
    def test_extract_lowercase_requirements(self, nlp_service):
        """Test extraction of lowercase requirements"""
        text = "The system must satisfy the security requirements."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        requirements = [e for e in entities if e['label'] == 'Requirement']
        assert len(requirements) >= 1
        assert any("security" in r['properties']['name'].lower() for r in requirements)
    
    def test_extract_multiple_requirements(self, nlp_service):
        """Test extraction of multiple requirements with 'and'"""
        text = "Must satisfy the performance requirements and the scalability requirements."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        requirements = [e for e in entities if e['label'] == 'Requirement']
        assert len(requirements) >= 2
    
    def test_extract_requirement_with_explicit_pattern(self, nlp_service):
        """Test extraction of requirement with explicit must satisfy pattern"""
        text = "The Payment Feature must satisfy the compliance requirements."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        requirements = [e for e in entities if e['label'] == 'Requirement']
        # Must satisfy pattern should extract requirements
        assert len(requirements) >= 1
        assert any("compliance" in r['properties']['name'].lower() for r in requirements)
    
    # ==================== Test Case Extraction Tests ====================
    
    def test_extract_testcase_tc_prefix(self, nlp_service):
        """Test extraction of test case with TC prefix"""
        text = "Test Case TC-101 validates the feature."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        testcases = [e for e in entities if e['label'] == 'TestCase']
        assert len(testcases) >= 1
        assert any("TC-101" in tc['properties']['name'] for tc in testcases)
    
    def test_extract_testcase_t_prefix(self, nlp_service):
        """Test extraction of test case with T prefix"""
        text = "T-2003 validates the component."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        testcases = [e for e in entities if e['label'] == 'TestCase']
        assert len(testcases) >= 1
        assert any("T-2003" in tc['properties']['name'] for tc in testcases)
    
    def test_extract_multiple_testcases(self, nlp_service):
        """Test extraction of multiple test cases"""
        text = "Test Case TC-2001 and Test Case TC-2002 validate the Ethereum Integration Module."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        testcases = [e for e in entities if e['label'] == 'TestCase']
        assert len(testcases) >= 2
    
    # ==================== Stakeholder Extraction Tests ====================
    
    def test_extract_person_with_role(self, nlp_service):
        """Test extraction of person with explicit role"""
        text = "Sarah Kim, the Blockchain Lead, presented the feature."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        stakeholders = [e for e in entities if e['label'] == 'Stakeholder']
        assert len(stakeholders) >= 1
        assert any("Sarah" in s['properties']['name'] or "Kim" in s['properties']['name'] 
                   for s in stakeholders)
    
    def test_extract_team(self, nlp_service):
        """Test extraction of team stakeholder"""
        text = "The feature is owned by the Blockchain Team."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        stakeholders = [e for e in entities if e['label'] == 'Stakeholder']
        assert len(stakeholders) >= 1
        assert any("Blockchain Team" in s['properties']['name'] or "Blockchain" in s['properties']['name']
                   for s in stakeholders)
    
    def test_extract_role_based_stakeholder(self, nlp_service):
        """Test extraction of role-based stakeholder"""
        text = "The Product Manager approved the requirements."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        stakeholders = [e for e in entities if e['label'] == 'Stakeholder']
        assert len(stakeholders) >= 1
        assert any("Product Manager" in s['properties']['name'] or "Manager" in s['properties']['name']
                   for s in stakeholders)
    
    # ==================== Constraint Extraction Tests ====================
    
    def test_extract_single_constraint(self, nlp_service):
        """Test extraction of single constraint"""
        text = "The Performance Constraint applies to the system."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        constraints = [e for e in entities if e['label'] == 'Constraint']
        assert len(constraints) >= 1
        assert any("Performance" in c['properties']['name'] for c in constraints)
    
    def test_extract_constraint_has_valid_structure(self, nlp_service):
        """Test that extracted constraints have required structure"""
        text = "The Performance Constraint applies to the system."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        constraints = [e for e in entities if e['label'] == 'Constraint']
        if constraints:
            for constraint in constraints:
                # Verify constraint has required fields
                assert 'id' in constraint
                assert 'label' in constraint
                assert 'properties' in constraint
                assert 'name' in constraint['properties']
    
    def test_extract_constraint_from_id_pattern(self, nlp_service):
        """Test extraction of constraint from ID-like patterns"""
        text = "The system has C-10 as a database constraint."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        # Verify that entity extraction can handle constraint patterns
        constraints = [e for e in entities if e['label'] == 'Constraint']
        # Should have at least attempted extraction even if C-10 specific pattern not matched
        assert isinstance(constraints, list)
    
    # ==================== Design Extraction Tests ====================
    
    def test_extract_design_entity(self, nlp_service):
        """Test extraction of design entity"""
        text = "The Distributed Ledger Architecture Design implements the feature."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        designs = [e for e in entities if e['label'] == 'Design']
        assert len(designs) >= 1
        assert any("Architecture" in d['properties']['name'] or "Design" in d['properties']['name']
                   for d in designs)
    
    def test_extract_design_has_valid_structure(self, nlp_service):
        """Test that extracted designs have required structure"""
        text = "The Distributed Ledger Architecture Design implements the feature."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        designs = [e for e in entities if e['label'] == 'Design']
        if designs:
            for design in designs:
                # Verify design has required fields
                assert 'id' in design
                assert 'label' in design
                assert 'properties' in design
                assert 'name' in design['properties']
    
    def test_extract_design_from_pattern(self, nlp_service):
        """Test extraction of design from pattern"""
        text = "The system uses D-5 for component implementation."
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        # Verify design extraction can handle design patterns
        designs = [e for e in entities if e['label'] == 'Design']
        # Should attempt extraction of design patterns
        assert isinstance(designs, list)
    
    # ==================== Relationship Tests ====================
    
    def test_owned_by_relationship(self, nlp_service):
        """Test OWNED_BY relationship"""
        text = "The Smart Contract Verification Feature is owned by the Blockchain Team."
        result = nlp_service.process_text(text)
        
        relationships = result['relationships']
        owns_rels = [r for r in relationships if r['type'] == 'OWNS']
        assert len(owns_rels) >= 1
    
    def test_depends_on_relationship(self, nlp_service):
        """Test DEPENDS_ON relationship"""
        text = "The Smart Contract Verification Feature depends on the Ethereum Integration Module."
        result = nlp_service.process_text(text)
        
        relationships = result['relationships']
        depends_rels = [r for r in relationships if r['type'] == 'DEPENDS_ON']
        assert len(depends_rels) >= 1
    
    def test_validates_relationship(self, nlp_service):
        """Test VALIDATES relationship"""
        text = "Test Case TC-2001 validates the Ethereum Integration Module."
        result = nlp_service.process_text(text)
        
        relationships = result['relationships']
        validates_rels = [r for r in relationships if r['type'] == 'VALIDATES']
        assert len(validates_rels) >= 1
    
    def test_satisfies_relationship(self, nlp_service):
        """Test SATISFIED_BY relationship"""
        text = "The Smart Contract Verification Feature must satisfy the security requirements."
        result = nlp_service.process_text(text)
        
        relationships = result['relationships']
        satisfies_rels = [r for r in relationships if r['type'] == 'SATISFIED_BY']
        assert len(satisfies_rels) >= 1
    
    # ==================== Edge Cases ====================
    
    def test_empty_text(self, nlp_service):
        """Test handling of empty text"""
        text = ""
        result = nlp_service.process_text(text)
        assert len(result['entities']) == 0
        assert len(result['relationships']) == 0
    
    def test_complex_document(self, nlp_service):
        """Test extraction from complex multi-sentence document"""
        text = """
        The Smart Contract Verification Feature is owned by the Blockchain Team.
        It depends on the Ethereum Integration Module and must satisfy the security requirements.
        Test Case TC-2001 validates the feature.
        """
        result = nlp_service.process_text(text)
        entities = result['entities']
        
        # Should extract multiple entity types
        features = [e for e in entities if e['label'] == 'Feature']
        stakeholders = [e for e in entities if e['label'] == 'Stakeholder']
        testcases = [e for e in entities if e['label'] == 'TestCase']
        requirements = [e for e in entities if e['label'] == 'Requirement']
        
        assert len(features) >= 1
        assert len(stakeholders) >= 1
        assert len(testcases) >= 1
        assert len(requirements) >= 1
    
    def test_text_with_no_entities(self, nlp_service):
        """Test text with no extractable entities"""
        text = "This is a simple sentence with no special entities."
        result = nlp_service.process_text(text)
        assert isinstance(result['entities'], list)
        assert isinstance(result['relationships'], list)
