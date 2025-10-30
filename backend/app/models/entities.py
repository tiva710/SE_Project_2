from enum import Enum

class Label(str, Enum):
    Feature = "Feature"
    Requirement = "Requirement"
    Stakeholder = "Stakeholder"
    Constraint = "Constraint"
    TestCase = "TestCase"
    Design = "Design"
    ConversationTurn = "ConversationTurn"
