import React from 'react';

function HelpView() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-teal-400 mb-6">Help & Documentation</h1>

      <div className="space-y-4">
        {[
          {
            title: 'Getting Started',
            content: 'Start by logging in through the Sidebar! Afterwards, feel free to upload a requirements discussion audio file or begin chatting in the conversation window with OpenAIs embedded LLM chatbot. A requirements graph fit with custom nodes will appear. You can continue refinement with the conversation, or download the graph for yourself! Please review the About page for more information and help-seeking resources. ',
          },
          {
            title: 'Understanding the Graph',
            content: 'The interactive requirements graph represents the relationships and dependencies that emerge from project discussions and transcripts. Each node in the graph corresponds to an entity extracted from conversations - such as requirements, features, tests, or stakeholders. Edges (connections) show how these entities relate: for example, a feature that depends on another, a test that validates a requirement, or a stakeholder that owns a deliverable. By exploring the graph, users can trace how ideas evolve from spoken discussions into structured, traceable requirements, helping teams spot missing links, redundant efforts, or unaligned expectations in real time.',
          },
        ].map((item, i) => (
          <div key={i} className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-teal-400 mb-2">{item.title}</h3>
            <p className="text-gray-300">{item.content}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-teal-400 mb-3">Need More Help?</h3>
        <p className="text-gray-300 mb-4">
          Check out our comprehensive documentation or reach out to the team.
        </p>
        <div className="flex gap-4">
          <a
            href="https://github.com/tiva710/SE_Project_2/wiki"
            className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg transition-colors"
          >
            View Documentation
          </a>
          <a
            href="https://docs.google.com/forms/d/e/1FAIpQLSfnR0p3P9GXqE0vYL3POOB-4eRcw-czH4RW3DlPySVc50C3LQ/viewform?usp=dialog"
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            Contact Support
          </a>
        </div>
      </div>
    </div>
  );
}

export default HelpView;
