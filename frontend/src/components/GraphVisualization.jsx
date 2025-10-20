import React from 'react';
import { Network } from 'lucide-react';

function GraphVisualization({ data }) {
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

  return (
    <div className="h-full bg-gray-900 rounded-lg border border-gray-700 p-6">
      <div className="space-y-4">
        {data.nodes.map(node => (
          <div key={node.id} className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xs font-bold ${
              node.type === 'Feature' ? 'bg-blue-600' :
              node.type === 'Stakeholder' ? 'bg-green-600' :
              node.type === 'Constraint' ? 'bg-red-600' :
              'bg-purple-600'
            }`}>
              {node.type[0]}
            </div>
            <div>
              <div className="font-medium">{node.name}</div>
              <div className="text-xs text-gray-500">{node.type}</div>
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-6">
        Note: This is a placeholder. Real graph will use react-force-graph when backend is ready.
      </p>
    </div>
  );
}

export default GraphVisualization;