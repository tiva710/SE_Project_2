import React from 'react';

function SettingsView() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-teal-400 mb-6">Settings</h1>

      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Graph Preferences</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="rounded" />
              <span className="text-sm">Auto-refresh graph on new messages</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="rounded" />
              <span className="text-sm">Show relationship labels</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="rounded" />
              <span className="text-sm">Enable physics simulation</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsView;
