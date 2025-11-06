import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Network, Filter, Eye } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';

function GraphVisualization({ graphData, graphReady, transcriptId }) {
  const [activeFilters, setActiveFilters] = useState({
    Requirement: true,
    Stakeholder: true,
    TestCase: true,
    Feature: true,
    Constraint: true,
    Team: true,
    Entity: true, // Temporary - in case nodes have Entity label
  });
  const [activeView, setActiveView] = useState('All Nodes');
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [err, setErr] = useState(null);
  const fgRef = useRef();

  const views = ['All Nodes', 'Stakeholder Impact', 'Feature Clusters'];

  const toggleFilter = (filterName) => {
    setActiveFilters((prev) => ({ ...prev, [filterName]: !prev[filterName] }));
  };

  const colorForType = (t) => {
    if (t === 'Feature') return '#2563eb';
    if (t === 'Stakeholder') return '#16a34a';
    if (t === 'Constraint') return '#dc2626';
    if (t === 'Requirement') return '#7c3aed';
    if (t === 'TestCase') return '#f59e0b';
    if (t === 'Team') return '#ec4899';
    return '#6b7280'; // fallback gray
  };

  const normalizeGraph = (res) => {
    const rawNodes = Array.isArray(res?.nodes) ? res.nodes : Array.isArray(res) ? res : [];
    const rawLinks = Array.isArray(res?.links) ? res.links : [];

    const nodes = rawNodes.map((n) => {
      // Get id from various possible locations
      const id = n.id ?? n.props?.id ?? String(n?.props?._id ?? '');
      
      // Get label from various locations - this is the node type
      const label = n.label ?? n.type ?? n.props?.label ?? 'Node';
      
      // Get display name from properties - THIS IS KEY FOR TOOLTIP
      // Priority: name property > role > title > extract from id
      let name = n.name ?? n.props?.name ?? n.props?.role ?? n.props?.title;
      
      // If still no name, try to extract from id
      if (!name && id) {
        // Remove recording_id suffix (e.g., "requirement:login_rec_123" -> "requirement:login")
        const cleanId = id.replace(/_rec_[a-f0-9]+$/i, '');
        // Extract the meaningful part after the colon
        const parts = cleanId.split(':');
        if (parts.length > 1) {
          name = parts[1].replace(/_/g, ' ');
        } else {
          name = cleanId.replace(/_/g, ' ');
        }
      }
      
      // Final fallback
      if (!name) {
        name = label;
      }

      console.log(`Node ${id}: label="${label}", name="${name}", props=`, n.props);

      return { 
        ...n, 
        id, 
        label,  // This is the type (Stakeholder, Requirement, etc.)
        name,   // This is the display name FOR TOOLTIP
        type: label // Also set type to match label for compatibility
      };
    });

    const nodeIds = new Set(nodes.map((n) => n.id));

    // Filter links to only include those where both nodes exist
    const links = rawLinks
      .map((l) => {
        const s =
          typeof l.source === 'object'
            ? l.source?.id
            : l.source ?? l.from ?? l.start ?? l.src ?? l.u ?? l.s;
        const t =
          typeof l.target === 'object'
            ? l.target?.id
            : l.target ?? l.to ?? l.end ?? l.dst ?? l.v ?? l.t;
        
        const relType = l.type ?? l.label ?? 'RELATED_TO';
        
        return { ...l, source: s, target: t, type: relType };
      })
      .filter((l) => {
        const hasSource = nodeIds.has(l.source);
        const hasTarget = nodeIds.has(l.target);
        
        if (!hasSource || !hasTarget) {
          console.warn(`Skipping link: ${l.source} -> ${l.target} (source exists: ${hasSource}, target exists: ${hasTarget})`);
        }
        
        return hasSource && hasTarget;
      });

    console.log('Normalized nodes:', nodes);
    console.log('Node labels found:', [...new Set(nodes.map(n => n.label))]);
    console.log('Valid links:', links.length, 'out of', rawLinks.length);
    
    return { nodes, links };
  };

  useEffect(() => {
    console.log('GV received graphData:', graphData);
    console.log('GV received graphReady:', graphReady);
    console.log('GV received transcriptId:', transcriptId);
    
    try {
      if (graphData && Array.isArray(graphData.nodes)) {
        const g = normalizeGraph(graphData);
        console.log('GV normalized:', g.nodes.length, 'nodes,', g.links.length, 'links');
        setGraph(g);
        setErr(null);
      } else {
        console.log('GV: no graphData or invalid shape');
        setGraph({ nodes: [], links: [] });
      }
    } catch (e) {
      console.error('GV normalize error:', e);
      setErr(e.message || 'Failed to normalize');
      setGraph({ nodes: [], links: [] });
    }
  }, [graphData, graphReady, transcriptId]);

  const filtered = useMemo(() => {
    // Use exact label matching
    const enabledTypes = new Set(
      Object.entries(activeFilters)
        .filter(([, on]) => on)
        .map(([k]) => k)
    );
    
    console.log('Active filter types:', [...enabledTypes]);
    
    const nodes = (graph.nodes ?? []).filter((n) => {
      const matches = enabledTypes.has(n.label) || enabledTypes.has(n.type);
      return matches;
    });
    
    const keep = new Set(nodes.map((n) => n.id));
    const links = (graph.links ?? []).filter((l) => {
      const s = typeof l.source === 'object' ? l.source?.id : l.source;
      const t = typeof l.target === 'object' ? l.target?.id : l.target;
      return keep.has(s) && keep.has(t);
    });
    
    console.log('Filtered result:', nodes.length, 'nodes,', links.length, 'links');
    
    return { nodes, links };
  }, [graph, activeFilters]);

  const nodeCanvasObject = (node, ctx, globalScale) => {
    const displayName = node.name || node.id || '';
    const color = colorForType(node.label || node.type);
    const r = 10;

    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.font = `${Math.max(8, 12 / globalScale)}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffffff';
    const letter = (node.label || node.type || '').charAt(0) || '?';
    ctx.fillText(letter, node.x, node.y);

    if (globalScale > 1.2) {
      ctx.font = `${Math.max(6, 10 / globalScale)}px Inter, sans-serif`;
      ctx.fillStyle = '#9ca3af';
      ctx.fillText(displayName, node.x, node.y + 16);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="bg-gray-800 border-b border-gray-700 p-3 space-y-3">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-gray-400" />
          <span className="text-xs font-semibold text-gray-400 uppercase">View:</span>
          <div className="flex flex-wrap gap-2">
            {views.map((view) => (
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

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-xs font-semibold text-gray-400 uppercase">Filters:</span>
          <div className="flex flex-wrap gap-2">
            {Object.keys(activeFilters).map((filter) => (
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

      <div className="flex-1 bg-gray-900 p-6 overflow-auto">
        <div className="space-y-4">
          {!filtered.nodes.length ? (
            <div className="text-center text-gray-500 py-8">
              <Network className="w-16 h-16 mx-auto opacity-30" />
              <p className="text-sm">{err || 'No nodes match current filters'}</p>
              {graph.nodes.length > 0 && (
                <p className="text-xs mt-2">
                  ({graph.nodes.length} nodes available - try adjusting filters)
                </p>
              )}
            </div>
          ) : (
            <div className="w-full" style={{ height: 520 }}>
              <ForceGraph2D
                ref={fgRef}
                graphData={filtered}
                width={undefined}
                height={undefined}
                backgroundColor="#111827"
                nodeLabel={(node) => `${node.label}: ${node.name || node.id}`}
                linkLabel={(link) => link.type || 'RELATED_TO'}
                linkColor={() => '#6b7280'}
                linkDirectionalParticles={2}
                linkDirectionalParticleWidth={2}
                linkWidth={2}
                cooldownTicks={90}
                nodeRelSize={6}
                nodeCanvasObject={nodeCanvasObject}
                onNodeClick={(node) => {
                  console.log('Node clicked:', node);
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default GraphVisualization;