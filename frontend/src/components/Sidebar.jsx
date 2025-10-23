import React, { useState } from 'react';
import {
  Upload,
  MessageSquare,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import axios from 'axios';

function Sidebar({ isOpen, onToggle, onClearGraph }) {
  const [uploading, setUploading] = useState(false);
  const [transcriptions, setTranscriptions] = useState([]);
  const [showTranscriptions, setShowTranscriptions] = useState(false);

  // 🎧 Handle audio upload
  const handleAudioUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('http://127.0.0.1:8000/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (res.data && res.data.entry) {
        setTranscriptions((prev) => [res.data.entry, ...prev]);
        alert(`✅ Transcribed: ${file.name}`);
      } else {
        alert('Error: No transcription returned from backend');
      }
    } catch (err) {
      console.error(err);
      alert('Error during transcription upload');
    } finally {
      setUploading(false);
    }
  };

  const sessionHistory = [
    { id: 1, name: 'Requirements Discussion', date: '2024-10-20', nodes: 12 },
    { id: 2, name: 'Feature Planning', date: '2024-10-19', nodes: 8 },
    { id: 3, name: 'Stakeholder Meeting', date: '2024-10-18', nodes: 15 },
  ];

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
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-teal-400">ReqTrace</h2>
        <button onClick={onToggle} className="p-1 hover:bg-gray-700 rounded">
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>

      {/* User Info */}
      <div className="bg-gray-700/50 rounded-lg p-3 border border-gray-600">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center">
            <User className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">Guest User</p>
            <p className="text-xs text-gray-400">Not logged in</p>
          </div>
        </div>
        <button className="w-full mt-2 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 rounded text-sm transition-colors">
          Login / Sign Up
        </button>
      </div>

      {/* 🎧 Audio Upload Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">
          Audio Upload
        </h3>
        <label className="block">
          <div className="flex items-center gap-2 px-4 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg cursor-pointer transition-colors">
            <Upload className="w-5 h-5" />
            <span className="font-medium">
              {uploading ? 'Uploading...' : 'Upload Audio'}
            </span>
          </div>
          <input
            type="file"
            className="hidden"
            onChange={handleAudioUpload}
            accept="audio/*"
            disabled={uploading}
          />
        </label>
        <p className="text-xs text-gray-500">Supported: MP3, WAV, M4A</p>
      </div>

      {/* ⚡ Quick Actions */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">
          Quick Actions
        </h3>

        {/* Show Transcriptions Button */}
        <button
          onClick={() => setShowTranscriptions(!showTranscriptions)}
          className="w-full flex items-center justify-between px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <span className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Show Transcriptions
          </span>
          {showTranscriptions ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>


        {/* Transcriptions Dropdown */}
        {showTranscriptions && (
          <div
            className="mt-2 bg-gray-800 border border-gray-700 rounded-lg p-2"
            style={{ maxHeight: '420px', overflowY: 'auto' }}   // list scroll
          >
            {transcriptions.length > 0 ? (
              transcriptions.map((t) => (
                <div
                  key={t.id}
                  className="mb-3 p-3 bg-gray-700 rounded-lg"
                >
                  {/* filename – no truncate; wrap long names */}
                  <p className="font-semibold text-teal-400 break-words">
                    {t.filename}
                  </p>

                  {/* FULL transcript – no line clamp; its own scroll if very long */}
                  <div className="mt-1 max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed text-sm text-gray-100">
                    {t.text}
                  </div>

                  <p className="text-[10px] text-gray-400 mt-2">{t.timestamp}</p>
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500 text-center py-2">
                No transcriptions yet.
              </p>
            )}
          </div>
        )}

        {/* Clear Graph */}
        <button
          onClick={onClearGraph}
          className="w-full flex items-center gap-2 px-4 py-3 bg-red-900/30 hover:bg-red-900/50 text-red-400 rounded-lg transition-colors"
        >
          <Trash2 className="w-5 h-5" />
          <span>Clear Graph</span>
        </button>
      </div>

      {/* 🕒 Session History */}
      <div className="space-y-3 flex-1">
        <h3 className="text-sm font-semibold text-gray-400 uppercase flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Session History
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {sessionHistory.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-4">
              No previous sessions
            </p>
          ) : (
            sessionHistory.map((session) => (
              <button
                key={session.id}
                className="w-full text-left px-3 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{session.name}</p>
                    <p className="text-xs text-gray-400">{session.date}</p>
                  </div>
                  <span className="text-xs text-teal-400 ml-2">
                    {session.nodes} nodes
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="pt-4 border-t border-gray-700">
        <p className="text-xs text-gray-500 text-center">
          💾 Sessions saved automatically
        </p>
      </div>
    </aside>
  );
}

export default Sidebar;
