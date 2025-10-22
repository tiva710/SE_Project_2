import React from 'react';

function HelpView() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-teal-400 mb-6">Help & Documentation</h1>

      <div className="space-y-4">
        {[
          {
            title: 'Getting Started',
            content: ''
          },
          {
            title: 'Understanding the Graph',
            content: ''
          },
          {
            title: 'View Modes',
            content: ''
          },
          {
            title: 'Exporting Data',
            content: ''
          }
        ].map((item, i) => (
          <div key={i} className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-teal-400 mb-2">{item.title}</h3>
            <p className="text-gray-300">{item.content}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-teal-400 mb-3">Need More Help?</h3>
        <p className="text-gray-300 mb-4">Check out our comprehensive documentation or reach out to the team.</p>
        <div className="flex gap-4">
          <button className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg transition-colors">
            View Documentation
          </button>
          <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
            Contact Support
          </button>
        </div>
      </div>
    </div>
  );
}

export default HelpView;