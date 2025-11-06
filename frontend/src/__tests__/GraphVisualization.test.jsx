import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GraphVisualization from '../components/GraphVisualization';
import { act } from '@testing-library/react';

jest.mock('react-force-graph-2d', () => {
  return require('react').forwardRef(({ graphData }, ref) => {
    return <div data-testid="force-graph" ref={ref} data-graph={JSON.stringify(graphData)}></div>;
  });
});

describe('GraphVisualization', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  const sampleData = {
    nodes: [
      { id: 1, name: 'Feature 1', label: 'Feature', type: 'Feature' },
      { id: 2, name: 'Stakeholder 1', label: 'Stakeholder', type: 'Stakeholder' },
      { id: 3, name: 'Constraint 1', label: 'Constraint', type: 'Constraint' },
    ],
    links: [{ source: 1, target: 2, type: 'RELATED_TO' }],
  };

  test('renders provided graph data', async () => {
    await act(async () => {
      render(<GraphVisualization graphData={sampleData} />);
    });
    expect(screen.getByTestId('force-graph')).toBeInTheDocument();
  });

  test('renders empty graph without crashing', async () => {
    await act(async () => {
      render(<GraphVisualization graphData={{ nodes: [], links: [] }} />);
    });
    expect(screen.getByText(/No nodes match current filters/i)).toBeInTheDocument();
  });

  test('renders gracefully when data is undefined', async () => {
    await act(async () => {
      render(<GraphVisualization />);
    });
    // Component should render without crashing
    expect(screen.getByText(/No nodes match current filters/i)).toBeInTheDocument();
  });

  test('can toggle filters', async () => {
    await act(async () => {
      render(<GraphVisualization graphData={sampleData} />);
    });
    
    const featureCheckbox = screen.getByLabelText(/Feature/i);
    expect(featureCheckbox).toBeChecked();
    
    await act(async () => {
      fireEvent.click(featureCheckbox);
    });
    
    expect(featureCheckbox).not.toBeChecked();
  });

  test('switching views does not crash', async () => {
    await act(async () => {
      render(<GraphVisualization graphData={sampleData} />);
    });

    const btn = screen.getByRole('button', { name: /Feature Clusters/i });
    
    await act(async () => {
      fireEvent.click(btn);
    });

    // View should be updated
    expect(btn).toHaveClass('bg-teal-600');
  });

  test('filtering Feature hides feature nodes', async () => {
    await act(async () => {
      render(<GraphVisualization graphData={sampleData} />);
    });
    
    const featureCheckbox = screen.getByLabelText(/Feature/i);
    
    await act(async () => {
      fireEvent.click(featureCheckbox);
    });

    // Force graph should have updated data without Feature nodes
    const fg = screen.getByTestId('force-graph');
    const parsed = JSON.parse(fg.dataset.graph);
    
    expect(parsed.nodes.some((n) => n.type === 'Feature' || n.label === 'Feature')).toBe(false);
  });

  test('links disappear when connected nodes are filtered out', async () => {
    await act(async () => {
      render(<GraphVisualization graphData={sampleData} />);
    });

    const featureCheckbox = screen.getByLabelText(/Feature/i);
    
    await act(async () => {
      fireEvent.click(featureCheckbox);
    });
    
    const fg = screen.getByTestId('force-graph');
    const parsed = JSON.parse(fg.dataset.graph);

    // Stakeholder node should still exist
    expect(parsed.nodes.some((n) => n.type === 'Stakeholder' || n.label === 'Stakeholder')).toBe(true);
    // Feature node should be removed
    expect(parsed.nodes.some((n) => n.type === 'Feature' || n.label === 'Feature')).toBe(false);
    // Links connected to removed Feature nodes should also be removed
    expect(parsed.links.some((l) => l.source === 1 || l.target === 1)).toBe(false);
  });
});