import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import HomeView from './pages/HomeView';
import AboutView from './pages/AboutView';
import SettingsView from './pages/SettingsView';
import HelpView from './pages/HelpView';
import { mockGraphData } from './utils/mockData';

function App() {
  const [activeView, setActiveView] = useState('home');
  const [graphData, setGraphData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSendMessage = (msg) => {
    setMessages([...messages, { id: Date.now(), text: msg, sender: 'user' }]);
    // Mock response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        text: 'Processing your request...', 
        sender: 'assistant' 
      }]);
      setGraphData(mockGraphData);
    }, 500);
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <Sidebar 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onUpload={() => setGraphData(mockGraphData)}
        onClearGraph={() => setGraphData(null)}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNav activeView={activeView} setActiveView={setActiveView} />

        <main className="flex-1 overflow-auto p-6">
          {activeView === 'home' && (
            <HomeView 
              graphData={graphData}
              messages={messages}
              onSendMessage={handleSendMessage}
            />
          )}
          {activeView === 'about' && <AboutView />}
          {activeView === 'settings' && <SettingsView />}
          {activeView === 'help' && <HelpView />}
        </main>
      </div>
    </div>
  );
}

export default App;