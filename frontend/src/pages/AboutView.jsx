import React from 'react';

function AboutView() {
  const repoUrl = "https://github.com/tiva710/SE_Project_2";
  const wikiUrl = "https://github.com/tiva710/SE_Project_2/wiki";
  const issuesUrl = "https://github.com/tiva710/SE_Project_2/issues";
  const docsUrl = "https://github.com/tiva710/SE_Project_2/tree/main/docs";

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Project Overview */}
      <div>
        <h1 className="text-4xl font-bold text-teal-400 mb-4">About ReqTrace-Graph</h1>
        <p className="text-gray-300 text-lg leading-relaxed mb-6">
          Requirements discussions often produce scattered, unstructured information that's difficult to track and trace. 
          ReqTrace-Graph automatically transforms natural language conversations with LLMs into interactive, navigable 
          knowledge graphs that reveal hidden dependencies, stakeholder impacts, and feature relationships.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href={repoUrl} target="_blank" rel="noopener noreferrer" 
             className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg font-medium transition-colors">
            View on GitHub
          </a>
          <a href={wikiUrl} target="_blank" rel="noopener noreferrer"
             className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors">
            Documentation Wiki
          </a>
          <a href={issuesUrl} target="_blank" rel="noopener noreferrer"
             className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors">
            Report Issues
          </a>
        </div>
      </div>

      {/* Key Features & Tech Stack */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-teal-400 mb-4">Key Features</h3>
          <ul className="space-y-2 text-gray-300">
            <li>✓ Real-time entity extraction from conversations</li>
            <li>✓ Automated relationship detection</li>
            <li>✓ Interactive graph visualization with multiple views</li>
            <li>✓ Dependency chain analysis</li>
            <li>✓ Stakeholder impact mapping</li>
            <li>✓ Bidirectional conversation-graph updates</li>
            <li>✓ Export capabilities (JSON, Cypher, RTM)</li>
          </ul>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-teal-400 mb-4">Tech Stack</h3>
          <ul className="space-y-2 text-gray-300">
            <li>• <strong>Frontend:</strong> React, Tailwind CSS, Vite</li>
            <li>• <strong>Backend:</strong> Python 3.9+, FastAPI</li>
            <li>• <strong>Database:</strong> Neo4j (Graph DB)</li>
            <li>• <strong>AI/ML:</strong> OpenAI API, spaCy NLP</li>
            <li>• <strong>Visualization:</strong> Pyvis, Plotly</li>
            <li>• <strong>CI/CD:</strong> GitHub Actions</li>
          </ul>
        </div>
      </div>

      {/* Stakeholders */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-teal-400 mb-4">Target Stakeholders</h3>
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4 text-gray-300">
          <div>
            <div className="font-semibold text-teal-300 mb-1">Requirements Engineers</div>
            <p className="text-sm text-gray-400">Capture and trace requirements efficiently</p>
          </div>
          <div>
            <div className="font-semibold text-teal-300 mb-1">Product Managers</div>
            <p className="text-sm text-gray-400">Visualize feature dependencies and impacts</p>
          </div>
          <div>
            <div className="font-semibold text-teal-300 mb-1">Software Architects</div>
            <p className="text-sm text-gray-400">Understand system constraints and relationships</p>
          </div>
          <div>
            <div className="font-semibold text-teal-300 mb-1">QA Teams</div>
            <p className="text-sm text-gray-400">Track requirement coverage and testing gaps</p>
          </div>
        </div>
      </div>

      {/* Documentation & Resources */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-teal-400 mb-4">Documentation & Resources</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold text-gray-200 mb-3">Getting Started</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href={`${wikiUrl}/Installation-Guide`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  📦 Installation Guide
                </a>
              </li>
              <li>
                <a href={`${wikiUrl}/Quick-Start`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  🚀 Quick Start Tutorial
                </a>
              </li>
              <li>
                <a href={`${wikiUrl}/Usage-Examples`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  💡 Usage Examples
                </a>
              </li>
              <li>
                <a href={`${docsUrl}/USE_CASES.md`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  📋 Use Cases
                </a>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-200 mb-3">Technical Documentation</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href={`${docsUrl}/API.md`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  🔌 API Reference
                </a>
              </li>
              <li>
                <a href={`${docsUrl}/TESTS.md`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  🧪 Testing Documentation
                </a>
              </li>
              <li>
                <a href={`${docsUrl}/DEPENDENCIES.md`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  📚 Dependencies
                </a>
              </li>
              <li>
                <a href={`${docsUrl}/CHANGELOG.md`} target="_blank" rel="noopener noreferrer"
                   className="text-teal-400 hover:text-teal-300 hover:underline">
                  📝 Changelog
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Support & Community */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-teal-400 mb-4">Support & Community</h3>
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-gray-200 mb-2">Get Help</h4>
            <p className="text-gray-400 text-sm mb-3">
              Need assistance? We're here to help through multiple channels:
            </p>
            <div className="flex flex-wrap gap-3">
              <a href={issuesUrl} target="_blank" rel="noopener noreferrer"
                 className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
                🐛 Report a Bug
              </a>
              <a href={`${issuesUrl}/new?labels=question`} target="_blank" rel="noopener noreferrer"
                 className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
                ❓ Ask a Question
              </a>
              <a href={`${issuesUrl}/new?labels=enhancement`} target="_blank" rel="noopener noreferrer"
                 className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
                💡 Request a Feature
              </a>
              <a href={`${docsUrl}/SUPPORT.md`} target="_blank" rel="noopener noreferrer"
                 className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
                📖 Support Guide
              </a>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-gray-200 mb-2">Contributing</h4>
            <p className="text-gray-400 text-sm mb-3">
              We welcome contributions! Check out our guidelines to get started:
            </p>
            <div className="flex flex-wrap gap-3">
              <a href={`${repoUrl}/blob/main/docs/CONTRIBUTING.md`} target="_blank" rel="noopener noreferrer"
                 className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg text-sm transition-colors">
                📝 Contribution Guidelines
              </a>
              <a href={`${repoUrl}/blob/main/docs/CODE_OF_CONDUCT.md`} target="_blank" rel="noopener noreferrer"
                 className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
                📜 Code of Conduct
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Project Info */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-teal-400 mb-4">Project Information</h3>
        <div className="grid md:grid-cols-2 gap-6 text-sm">
          <div>
            <h4 className="font-semibold text-gray-200 mb-2">License</h4>
            <p className="text-gray-400 mb-1">MIT License - Free and Open Source</p>
            <a href={`${repoUrl}/blob/main/docs/LICENCE.md`} target="_blank" rel="noopener noreferrer"
               className="text-teal-400 hover:text-teal-300 hover:underline">
              View License Details
            </a>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-200 mb-2">Citation</h4>
            <p className="text-gray-400 mb-1">Use this project in your research?</p>
            <a href={`${repoUrl}/blob/main/docs/CITATION.md`} target="_blank" rel="noopener noreferrer"
               className="text-teal-400 hover:text-teal-300 hover:underline">
              How to Cite
            </a>
          </div>

          <div>
            <h4 className="font-semibold text-gray-200 mb-2">Test Coverage</h4>
            <p className="text-gray-400">130+ test cases ensuring reliability</p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-200 mb-2">Accessibility</h4>
            <p className="text-gray-400">WCAG 2.1 compliant design</p>
          </div>
        </div>
      </div>

      {/* Roadmap */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-teal-400 mb-4">Project Roadmap</h3>
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-green-400 mb-2">✓ Completed (October Milestones)</h4>
            <ul className="space-y-1 text-sm text-gray-300 ml-4">
              <li>• Real-time entity extraction from LLM conversations</li>
              <li>• Automated relationship detection and graph construction</li>
              <li>• Interactive graph visualization with multiple perspectives</li>
              <li>• Conversation-to-graph bidirectional updates</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold text-teal-400 mb-2">→ In Progress (November Milestones)</h4>
            <ul className="space-y-1 text-sm text-gray-300 ml-4">
              <li>• Advanced dependency chain analysis</li>
              <li>• Multi-conversation merge and conflict resolution</li>
              <li>• Export capabilities (RTM format, JSON, Cypher)</li>
              <li>• Collaborative multi-user editing with version control</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Team */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 text-center">
        <h3 className="text-xl font-semibold text-teal-400 mb-3">Built with ❤️ by the ReqTrace Team</h3>
        <p className="text-gray-400 text-sm">
          A Software Engineering Project focused on innovative requirements traceability solutions
        </p>
      </div>
    </div>
  );
}

export default AboutView;