import React, {useContext} from 'react';
import { AuthContext } from "../context/AuthContext";
import { Upload, MessageSquare, Trash2, ChevronLeft, ChevronRight, Clock, User } from 'lucide-react';
import LoginButton from "./LoginButton";

function Sidebar({ isOpen, onToggle, onUpload, onClearGraph }) {
  const { user, login, logout } = useContext(AuthContext);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      onUpload();
    }
  };

  // Mock session history: will be replaced w real data from backend
  const sessionHistory = user 
  ? [
    { id: 1, name: 'Requirements Discussion', date: '2024-10-20', nodes: 12 },
    { id: 2, name: 'Feature Planning', date: '2024-10-19', nodes: 8 },
    { id: 3, name: 'Stakeholder Meeting', date: '2024-10-18', nodes: 15 },
  ]
  : [];

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

      {/* Login/Signup Section */}
      <div className="bg-gray-700/50 rounded-lg p-3 border border-gray-600">
        <div className="flex items-center gap-3">
          {user?.picture ? (
            <img
              src={user.picture}
              alt="User avatar"
              className="w-10 h-10 rounded-full"
            />
          ) : (         
            <div className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center">
              <User className="w-5 h-5" />
            </div>
          )}
          <div className="flex-1">
            <p className="text-sm font-medium">
              {user ? user.email : "Guest User"}
            </p>
            <p className="text-xs text-gray-400">
              {user ? user.email: "Not logged in"}
            </p>
          </div>
        </div>
        {!user && <LoginButton/>}
        {user && (
          <button
            onClick={logout}
            className="w-full mt-2 px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
          >Logout</button>
        )}
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

      {/* Session History */}
      <div className="space-y-3 flex-1">
        <h3 className="text-sm font-semibold text-gray-400 uppercase flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Session History
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {sessionHistory.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-4">No previous sessions</p>
          ) : (
            sessionHistory.map(session => (
              <button
                key={session.id}
                className="w-full text-left px-3 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{session.name}</p>
                    <p className="text-xs text-gray-400">{session.date}</p>
                  </div>
                  <span className="text-xs text-teal-400 ml-2">{session.nodes} nodes</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-gray-700">
        <p className="text-xs text-gray-500 text-center">
          💾 Sessions saved automatically
        </p>
      </div>
    </aside>
  );
}

export default Sidebar;