import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Network, Filter, Eye } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';
import {
  getOverview,
  getStakeholdersOverview,
  getFeaturesOverview,
  getStakeholderNeighborhood,
  getFeatureNeighborhood,
} from '../api/index.jsx'; // adjust path if needed

function GraphVisualization({ data }) {
  const [activeFilters, setActiveFilters] = useState({
    Features: true,
    Stakeholders: true,
    Constraints: true,
    Requirements: true,
  });
  const [activeView, setActiveView] = useState('All Nodes');
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const fgRef = useRef();

  const views = ['All Nodes', 'Dependency Chain', 'Stakeholder Impact', 'Feature Clusters'];

  const toggleFilter = (filterName) => {
    setActiveFilters(prev => ({ ...prev, [filterName]: !prev[filterName] }));
  };

  // Color palette consistent with your badges
  const colorForType = (t) => {
    if (t === 'Feature') return '#2563eb';      // blue-600
    if (t === 'Stakeholder') return '#16a34a';  // green-600
    if (t === 'Constraint') return '#dc2626';   // red-600
    return '#7c3aed';                           // purple-600 (Requirement/other)
  };

  // Normalize backend payload -> { nodes: [{id,name,type,...}], links: [{source,target,...}] }
  const normalizeGraph = (res) => {
    const rawNodes = Array.isArray(res?.nodes) ? res.nodes : Array.isArray(res) ? res : [];
    const rawLinks = Array.isArray(res?.links) ? res.links : [];

    const nodes = rawNodes.map(n => {
      // Backend sample:
      // { id, label: "Stakeholder", props: { name, role, id } }
      const id = n.id ?? n.props?.id;
      const type = n.type ?? n.label ?? 'Node';
      const name =
        n.name ??
        n.props?.name ??
        n.props?.role ??
        n.props?.id ??
        n.id ??
        String(id);

      return {
        ...n,
        id,
        type,
        name,
      };
    });

    const index = new Set(nodes.map(n => n.id));
    const links = rawLinks
      .map(l => {
        // Allow various shapes: {source,target} or {from,to} etc.
        const source = l.source ?? l.from ?? l.start ?? l.src ?? l.u ?? l.s;
        const target = l.target ?? l.to ?? l.end ?? l.dst ?? l.v ?? l.t;
        return { ...l, source, target };
      })
      .filter(l => index.has(typeof l.source === 'object' ? l.source?.id : l.source)
                && index.has(typeof l.target === 'object' ? l.target?.id : l.target));

    return { nodes, links };
  };

  const fetchGraphForView = async (view) => {
    setLoading(true);
    setErr(null);
    try {
      if (view === 'All Nodes') {
        const [feat, stake] = await Promise.all([
          getOverview(500)
        ]);
        const A = normalizeGraph(feat);
        const B = normalizeGraph(stake);
        // de-duplicate nodes by id
        const seen = new Set();
        const nodes = [...A.nodes, ...B.nodes].filter(n => {
          if (seen.has(n.id)) return false;
          seen.add(n.id);
          return true;
        });
        const links = [...A.links, ...B.links];
        setGraph({ nodes, links });
        return;
      }

      if (view === 'Stakeholder Impact') {
        const res = await getStakeholdersOverview(500);
        setGraph(normalizeGraph(res));
        return;
      }

      if (view === 'Feature Clusters') {
        const res = await getFeaturesOverview(500);
        setGraph(normalizeGraph(res));
        return;
      }

      if (view === 'Dependency Chain') {
        // Try a small neighborhood around first node (can wire to a selection later)
        const seed =
          graph.nodes.find(n => n.type === 'Feature')?.id ??
          graph.nodes.find(n => n.type === 'Stakeholder')?.id ??
          null;

        if (seed) {
          const [a, b] = await Promise.allSettled([
            getFeatureNeighborhood(seed, 1, 500),
            getStakeholderNeighborhood(seed, 1, 500),
          ]);
          const candidate =
            (a.status === 'fulfilled' && a.value) ||
            (b.status === 'fulfilled' && b.value) ||
            { nodes: [], links: [] };
          setGraph(normalizeGraph(candidate));
        } else {
          const res = await getFeaturesOverview(200);
          setGraph(normalizeGraph(res));
        }
        return;
      }

      setGraph({ nodes: [], links: [] });
    } catch (e) {
      setErr(e.message || 'Failed to load graph');
      setGraph({ nodes: [], links: [] });
    } finally {
      setLoading(false);
    }
  };

  // Initial load: prefer provided data, otherwise fetch
  useEffect(() => {
    if (data?.nodes || data?.links) {
      setGraph(normalizeGraph(data));
    } else {
      fetchGraphForView(activeView);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reload on view change if not controlled by parent
  useEffect(() => {
    if (!data) fetchGraphForView(activeView);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeView]);

  // Apply type filters
  const filtered = useMemo(() => {
    const enabledTypes = new Set(
      Object.entries(activeFilters)
        .filter(([, on]) => on)
        .map(([k]) => k.replace(/s$/, '')) // Features -> Feature
    );
    const nodes = (graph.nodes ?? []).filter(n => enabledTypes.has(n.type));
    const keep = new Set(nodes.map(n => n.id));
    const links = (graph.links ?? []).filter(l => {
      const s = typeof l.source === 'object' ? l.source?.id : l.source;
      const t = typeof l.target === 'object' ? l.target?.id : l.target;
      return keep.has(s) && keep.has(t);
    });
    return { nodes, links };
  }, [graph, activeFilters]);

  const nodeCanvasObject = (node, ctx, globalScale) => {
    const label = node.name || node.id || '';
    const color = colorForType(node.type);
    const r = 10;

    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.font = `${Math.max(8, 12 / globalScale)}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffffff';
    const letter = (node.type || '').charAt(0) || '?';
    ctx.fillText(letter, node.x, node.y);

    if (globalScale > 1.2) {
      ctx.font = `${Math.max(6, 10 / globalScale)}px Inter, sans-serif`;
      ctx.fillStyle = '#9ca3af';
      ctx.fillText(label, node.x, node.y + 16);
    }
  };

  if (loading && (graph.nodes?.length ?? 0) === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center space-y-3">
          <Network className="w-16 h-16 mx-auto opacity-30" />
          <p className="text-sm">Loading graph…</p>
        </div>
      </div>
    );
  }

  if (!loading && err && (graph.nodes?.length ?? 0) === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center space-y-3">
          <Network className="w-16 h-16 mx-auto opacity-30" />
          <p className="text-sm">Failed to load graph</p>
          <p className="text-xs">{err}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Controls Bar */}
      <div className="bg-gray-800 border-b border-gray-700 p-3 space-y-3">
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
          {filtered.nodes.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-sm">No nodes match current filters</p>
            </div>
          ) : (
            <div className="w-full" style={{ height: 520 }}>
              <ForceGraph2D
                ref={fgRef}
                graphData={filtered}
                width={undefined}
                height={undefined}
                backgroundColor="#111827"
                linkColor={() => '#6b7280'}
                linkDirectionalParticles={0}
                linkWidth={1}
                cooldownTicks={90}
                nodeRelSize={6}
                nodeCanvasObject={nodeCanvasObject}
              />
            </div>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-6 text-center">
          Note: This normalizes backend nodes (id, label, props) to the component format (id, name, type).
        </p>
      </div>
    </div>
  );
}

export default GraphVisualization;
