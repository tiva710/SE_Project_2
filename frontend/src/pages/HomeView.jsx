import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Network,
  MessageSquare,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  GripVertical,
} from 'lucide-react';
import GraphVisualization from '../components/GraphVisualization';
import ChatInterface from '../components/ChatInterface';

function HomeView({ graphData, messages, onSendMessage }) {
  const [splitPosition, setSplitPosition] = useState(50); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseMove = useCallback(
    (e) => {
      if (!isDragging || !containerRef.current) return;

      const container = containerRef.current;
      const rect = container.getBoundingClientRect();
      const newPosition = ((e.clientX - rect.left) / rect.width) * 100;

      // Constrain between 20% and 80%
      if (newPosition >= 20 && newPosition <= 80) {
        setSplitPosition(newPosition);
      }
    },
    [isDragging]
  );

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, handleMouseMove]);

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-teal-400 mb-2">
          Requirements Traceability Graph Generator
        </h1>
        <p className="text-gray-400">
          Upload a document, start a conversation, or transcribe audio to generate your interactive
          knowledge graph.
        </p>
      </div>

      {/* Main Content Area - Resizeable Split View */}
      <div ref={containerRef} className="flex-1 flex gap-0 min-h-0 relative">
        {/* Graph Visualization */}
        <div
          style={{ width: `${splitPosition}%` }}
          className="bg-gray-800 rounded-l-xl border border-gray-700 overflow-hidden flex flex-col"
        >
          <div className="p-4 border-b border-gray-700 flex items-center justify-between bg-gray-800">
            <h2 className="font-semibold flex items-center gap-2">
              <Network className="w-5 h-5 text-teal-400" />
              Knowledge Graph
            </h2>
            <div className="flex items-center gap-2">
              <button
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <button
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                title="Fullscreen"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors" title="Export">
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            <GraphVisualization data={graphData} />
          </div>
        </div>

        {/* Draggable Divider */}
        <div
          onMouseDown={handleMouseDown}
          className={`w-1 bg-gray-700 hover:bg-teal-500 cursor-col-resize flex items-center justify-center relative group transition-colors ${isDragging ? 'bg-teal-500' : ''}`}
        >
          <div className="absolute inset-y-0 -left-1 -right-1 flex items-center justify-center">
            <GripVertical className="w-4 h-4 text-gray-600 group-hover:text-teal-400" />
          </div>
        </div>

        {/* Chat Interface */}
        <div
          className="bg-gray-800 rounded-r-xl border border-gray-700 overflow-hidden flex flex-col"
          style={{ width: `${100 - splitPosition}%` }}
        >
          <div className="p-4 border-b border-gray-700 bg-gray-800">
            <h2 className="font-semibold flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-teal-400" />
              Conversation
            </h2>
          </div>
          <ChatInterface messages={messages} onSendMessage={onSendMessage} />
        </div>
      </div>
    </div>
  );
}

export default HomeView;
