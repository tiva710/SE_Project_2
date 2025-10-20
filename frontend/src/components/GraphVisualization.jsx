import React, { useState } from 'react';
import { Network, Filter, Eye } from 'lucide-react';

function GraphVisualization({ data }) {
  const [activeFilters, setActiveFilters] = useState({
    Features: true,
    Stakeholders: true,
    Constraints: true,
    Requirements: true,
  });

  const [activeView, setActiveView] = useState('All Nodes');

  const toggleFilter = (filterName) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterName]: !prev[filterName]
    }));
  };

  const views = ['All Nodes', 'Dependency Chain', 'Stakeholder Impact', 'Feature Clusters'];

  if (!data) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center space-y-3">
          <Network className="w-16 h-16 mx-auto opacity-30" />
          <p className="text-sm">No graph data yet</p>
          <p className="text-xs">Upload a file or start chatting to generate your graph</p>
        </div>
      </div>
    );
  }

  // Filter nodes based on active filters
  const filteredNodes = data.nodes.filter(node => activeFilters[node.type + 's'] !== false);

  return (
    <div className="h-full flex flex-col">
      {/* Controls Bar */}
      <div className="bg-gray-800 border-b border-gray-700 p-3 space-y-3">
        {/* View Selector */}
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-gray-400" />
          <span className="text-xs font-semibold text-gray-400 uppercase">View:</span>
          <div className="flex flex-wrap gap-2">
            {views.map(view => (
              <button
                key={view}
                onClick={() => setActiveView(view)}
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  activeView === view
                    ? 'bg-teal-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {view}
              </button>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-xs font-semibold text-gray-400 uppercase">Filters:</span>
          <div className="flex flex-wrap gap-2">
            {Object.keys(activeFilters).map(filter => (
              <label
                key={filter}
                className="flex items-center gap-1.5 px-2 py-1 bg-gray-700 rounded cursor-pointer hover:bg-gray-600 transition-colors"
              >
                <input
                  type="checkbox"
                  checked={activeFilters[filter]}
                  onChange={() => toggleFilter(filter)}
                  className="rounded w-3 h-3"
                />
                <span className="text-xs">{filter}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Graph Area */}
      <div className="flex-1 bg-gray-900 p-6 overflow-auto">
        <div className="space-y-4">
          {filteredNodes.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-sm">No nodes match current filters</p>
            </div>
          ) : (
            filteredNodes.map(node => (
              <div key={node.id} className="flex items-center gap-3 group">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xs font-bold transition-transform group-hover:scale-110 ${
                  node.type === 'Feature' ? 'bg-blue-600' :
                  node.type === 'Stakeholder' ? 'bg-green-600' :
                  node.type === 'Constraint' ? 'bg-red-600' :
                  'bg-purple-600'
                }`}>
                  {node.type[0]}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{node.name}</div>
                  <div className="text-xs text-gray-500">{node.type}</div>
                </div>
              </div>
            ))
          )}
        </div>
        <p className="text-xs text-gray-500 mt-6 text-center">
          Note: This is a placeholder. Real graph will use react-force-graph when backend is ready.
        </p>
      </div>
    </div>
  );
}

export default GraphVisualization;