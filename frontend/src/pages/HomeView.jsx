import React from 'react';
import { Network, MessageSquare, Search, ZoomIn, ZoomOut, Maximize2, Download } from 'lucide-react';
import GraphVisualization from '../components/GraphVisualization';
import ChatInterface from '../components/ChatInterface';

function HomeView({ graphData, messages, onSendMessage }) {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-teal-400 mb-2">Requirements Traceability Graph Generator</h1>
        <p className="text-gray-400">Upload a document, start a conversation, or transcribe audio to generate your interactive knowledge graph.</p>
      </div>

      {/* Main Content Area - Split View */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
        {/* Graph Visualization */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-700 flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2">
              <Network className="w-5 h-5 text-teal-400" />
              Knowledge Graph
            </h2>
            <div className="flex items-center gap-2">
              <button className="p-2 hover:bg-gray-700 rounded-lg" title="Search">
                <Search className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-gray-700 rounded-lg" title="Zoom In">
                <ZoomIn className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-gray-700 rounded-lg" title="Zoom Out">
                <ZoomOut className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-gray-700 rounded-lg" title="Fullscreen">
                <Maximize2 className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-gray-700 rounded-lg" title="Export">
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 p-4">
            <GraphVisualization data={graphData} />
          </div>
        </div>

        {/* Chat Interface */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-700">
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