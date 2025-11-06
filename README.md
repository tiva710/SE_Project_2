# ReqTrace
---

## Overview 
**ReqTrace** is a tool that automatically constructs interactive knowledge graphs from requirements discussions. Discussions can come from uploaded transcripts or conversations with an embedded LLM. As conversations and discussions unfold, the system will identify entities (e.g. features, stakeholders, contraints), extract relationships, and build a navigable graph showing how requirements connect. Stakeholders can explore and refine the graph through continued conversations and preferences. 

---

## Intended Users 
ReqTrace is intended for software engineers, project managers, and stakeholders involved in the requirements engineering process. It supports anyone responsible for eliciting, analyzing, or maintaining system requirements, particularly in collaborative or evolving project environments. Researchers may also use ReqTrace for exploring automated requirements extraction or graph-based documentation tools. 

For detailed use cases, see [USE_CASES.md](docs/USE_CASES.md)

---

## Road Map 
Completed Milestones (October)
- User Auth + Frontend: JWT login/signup · React UI · role scaffolding · responsive dashboard
- Audio Upload + Transcription: FastAPI upload · OpenAI Whisper speech-to-text · auto storage
- Transcript Vectorisation + AI Chat: FAISS embeddings · semantic search · LLM drafts user reqs
- NER-driven Graph Build: NER on transcripts extracts entities to create nodes/edges.
- Graph Visualisation: Neo4j + React Flow · nodes (Req/Feat/Test/Stakeholder) · edges (depends/validates/owns)

Future Milestones (November)
- Save/load conversation sessions 
-- session versioning 
-- resume interrupted conversations 
-- session comparison 
-- export conversation history
- Graph Comparison - 
-- Compare two graph versions 
-- highlight differences 
-- merge graphs
-- track evolution over time
- Custom Graph Views & Perspectives  
-- Save personalized graph layouts 
-- stakeholder-specific views 
-- dependency-focused views 
-- feature cluster views 
-- timeline view
- Software Design Document Generation 
-- Automatically generate architecture diagrams from graph structure 
-- create component specifications from requirement nodes 
-- generate interface designs from relationships 
-- produce design rationale from conversation context 
-- export design docs in standard formats (Markdown/PDF)


---

## Quick Start 
See [INSTALL.md](docs/INSTALL.md) and [USAGE.md](docs/USAGE.md) for step-by-step instructions.  

Quick Start snippet: 

Backend: 

```bash
cd backend
python3 -m venv .venv        # create virtual environment
source .venv/bin/activate    # activate on macOS/Linux
# OR for Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install --upgrade pip
brew install ffmpeg
python -m spacy download en_core_web_sm
python -m coreferee install en
/Applications/Python\ 3.11/Install\ Certificates.command   #for mac installation
pip install spacy-transformers 
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.4.1/en_core_web_lg-3.4.1-py3-none-any.whl
uvicorn main:app --reload
```

Frontend: 
```bash
cd frontend
npm install 
npm run dev
```
---

##  ReqTrace Demo
Watch a quick video of ReqTrace in action! 

---

## Documentation
Complete documentation is available in the [Wiki](https://github.com/tiva710/SE_Project_2/wiki)!

---

## Badges
License: 
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Doi: 
[![DOI](https://img.shields.io/badge/DOI-10.5281/zenodo.17544380-blue.svg)](https://doi.org/10.5281/zenodo.17544380)

### Tests & Code Quality
[![Backend CI](https://github.com/tiva710/SE_Project_2/actions/workflows/main.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/main.yml)
[![Frontend CI](https://github.com/tiva710/SE_Project_2/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/frontend-tests.yml)

All 3 are in one workflow ```lint.yml```

- ESLint: [![ESLint](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml)
- Stylelint: [![Stylelint](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml)
- Prettier: [![Prettier](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml)
---

## Support & Contact
- [GitHub isses](https://github.com/tiva710/SE_Project_2/issues)
- [Support Form](https://docs.google.com/forms/d/e/1FAIpQLSfnR0p3P9GXqE0vYL3POOB-4eRcw-czH4RW3DlPySVc50C3LQ/viewform)

--- 

## Licence & Citation 
- [MIT License](docs/LICENSE.md)
- [Citation](docs/CITATION.md)

---
## Contributors 
- [Tiva Rocco](https://github.com/tiva710)
- [Anusha Upadhyay](https://github.com/AnushaU1111)
- [Rujuta Palimkar](https://github.com/ruju4a)
- [Aayushi Masurekar](https://github.com/aayushimasurekar)
