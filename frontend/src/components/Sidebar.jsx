import React from 'react';
import { Upload, MessageSquare, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';

function Sidebar({ isOpen, onToggle, onUpload, onClearGraph }) {
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      onUpload();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed left-4 top-1/2 -translate-y-1/2 bg-gray-800 p-2 rounded-r-lg hover:bg-gray-700 z-50"
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    );
  }

  return (
    <aside className="w-80 bg-gray-800 border-r border-gray-700 p-6 flex flex-col gap-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-teal-400">ReqTrace</h2>
        <button onClick={onToggle} className="p-1 hover:bg-gray-700 rounded">
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>

      {/* Upload Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Document Upload</h3>
        <label className="block">
          <div className="flex items-center gap-2 px-4 py-3 bg-teal-600 hover:bg-teal-700 rounded-lg cursor-pointer transition-colors">
            <Upload className="w-5 h-5" />
            <span className="font-medium">Upload File</span>
          </div>
          <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf,.docx,.txt" />
        </label>
        <p className="text-xs text-gray-500">Supported: PDF, DOCX, TXT</p>
      </div>

      {/* Quick Actions */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Quick Actions</h3>
        <button className="w-full flex items-center gap-2 px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
          <MessageSquare className="w-5 h-5" />
          <span>Show Transcriptions</span>
        </button>
        <button 
          onClick={onClearGraph}
          className="w-full flex items-center gap-2 px-4 py-3 bg-red-900/30 hover:bg-red-900/50 text-red-400 rounded-lg transition-colors"
        >
          <Trash2 className="w-5 h-5" />
          <span>Clear Graph</span>
        </button>
      </div>

      {/* Graph Views */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Graph Views</h3>
        <div className="space-y-2">
          {['Dependency Chain', 'Stakeholder Impact', 'Feature Clusters', 'All Nodes'].map(view => (
            <button
              key={view}
              className="w-full text-left px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-sm"
            >
              {view}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Filters</h3>
        <div className="space-y-2">
          {['Features', 'Stakeholders', 'Constraints', 'Requirements'].map(filter => (
            <label key={filter} className="flex items-center gap-2 text-sm">
              <input type="checkbox" defaultChecked className="rounded" />
              <span>{filter}</span>
            </label>
          ))}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;