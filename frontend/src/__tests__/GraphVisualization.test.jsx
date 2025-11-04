import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GraphVisualization from '../components/GraphVisualization';
import * as api from '../api/index.jsx';
import { act } from '@testing-library/react';

jest.mock('../api/index.jsx');

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
      { id: 1, name: 'Feature 1', type: 'Feature' },
      { id: 2, name: 'Stakeholder 1', type: 'Stakeholder' },
      { id: 3, name: 'Constraint 1', type: 'Constraint' },
    ],
    links: [{ source: 1, target: 2 }],
  };

  test('renders provided graph data', async () => {
    render(<GraphVisualization data={sampleData} />);
    expect(screen.getByTestId('force-graph')).toBeInTheDocument();
  });

  test('renders empty graph without crashing', () => {
    render(<GraphVisualization data={{ nodes: [], links: [] }} />);
    expect(screen.getByText(/No nodes match current filters/i)).toBeInTheDocument();
  });

  test('renders gracefully when data is undefined', () => {
    render(<GraphVisualization />);
    expect(screen.getByText(/Loading graph/i)).toBeInTheDocument();
  });

  test('can toggle filters', () => {
    render(<GraphVisualization data={sampleData} />);
    const featureCheckbox = screen.getByLabelText(/Features/i);
    expect(featureCheckbox).toBeChecked();
    fireEvent.click(featureCheckbox);
    expect(featureCheckbox).not.toBeChecked();
  });

  test('switching views triggers API calls', async () => {
    api.getFeaturesOverview.mockResolvedValue(sampleData);
    api.getStakeholdersOverview.mockResolvedValue(sampleData);

    render(<GraphVisualization />);

    const btn = await screen.findByRole('button', { name: /Feature Clusters/i });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(api.getFeaturesOverview).toHaveBeenCalled();
    });
  });

  test('filtering Features hides feature nodes', () => {
    render(<GraphVisualization data={sampleData} />);
    const featureCheckbox = screen.getByLabelText(/Features/i);
    fireEvent.click(featureCheckbox);

    expect(screen.queryByText(/Feature 1/i)).not.toBeInTheDocument();
  });

  test('links disappear when connected nodes are filtered out', () => {
    render(<GraphVisualization data={sampleData} />);

    const featureCheckbox = screen.getByLabelText(/Features/i);
    act(() => {
      fireEvent.click(featureCheckbox);
    });
    const fg = screen.getByTestId('force-graph');
    const parsed = JSON.parse(fg.dataset.graph);

    // Stakeholder node should still exist
    expect(parsed.nodes.some((n) => n.type === 'Stakeholder')).toBe(true);
    // Feature node should be removed
    expect(parsed.nodes.some((n) => n.type === 'Feature')).toBe(false);
    // Links connected to removed Feature nodes should also be removed
    expect(parsed.links.some((l) => l.source === 1 || l.target === 1)).toBe(false);
  });
});
