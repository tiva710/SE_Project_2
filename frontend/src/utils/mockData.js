export const mockGraphData = {
  nodes: [
    { id: 1, name: 'User Authentication', type: 'Feature' },
    { id: 2, name: 'Product Manager', type: 'Stakeholder' },
    { id: 3, name: 'Security Compliance', type: 'Constraint' },
    { id: 4, name: 'Login Requirement', type: 'Requirement' },
    { id: 5, name: 'Password Reset', type: 'Feature' },
    { id: 6, name: 'Security Team', type: 'Stakeholder' },
  ],
  edges: [
    { source: 1, target: 4, type: 'REFINES' },
    { source: 4, target: 3, type: 'CONSTRAINS' },
    { source: 1, target: 2, type: 'AFFECTS' },
    { source: 5, target: 1, type: 'DEPENDS_ON' },
    { source: 3, target: 6, type: 'OWNED_BY' },
  ],
};
