Flow-of-events style use cases regarding stakeholders and expected flows
---
### UC 1: Upload and Transcribe Requirements Discussion
Primary Actor: Business Analyst

Preconditions:

&emsp;1. User is authenticated via Oath2.

&emsp;2. Audio file is available locally.

Main Flow:

&emsp;1. User navigates to “Upload Transcripts.”

&emsp;2. System prompts user to select an audio file.

&emsp;3. User uploads file; backend receives it via FastAPI.

&emsp;4. System processes file with Whisper for transcription.

&emsp;5. Transcript is stored and displayed in UI.

Subflows:

&emsp;4a. If file upload is not an audio file system prompts user to upload correct file type 

Alternate Flows:

&emsp;A1. File upload fails → display “Upload failed” and prompt retry.

&emsp;A2. Whisper API error → display “Transcription unavailable, please retry later.”

Postconditions:

&emsp;Transcript is available for vectorization and graph generation.

---

### UC 2: Generate Interactive Knowledge Graph

Primary Actor: Requirements Engineer

Preconditions:

&emsp;1. At least one transcript is uploaded

Main Flow:

&emsp;1. System runs NER to extract entities (Requirements, Features, Stakeholders).

&emsp;2. Entities converted into nodes; relationships inferred.

&emsp;3. Graph stored in Neo4j.

&emsp;4. Graph displayed using React Flow.

Subflows:

&emsp;3a. Ambiguous entities trigger user confirmation dialog.

Alternate Flows:

&emsp;A1. No entities extracted → prompt user to tag manually.

Postconditions:

&emsp;Graph nodes and edges persisted in database and visible to user.

---

### UC 3: Explore Requirements Graph

Primary Actor: Product Manager

Preconditions:

&emsp;Graph exists and user has access permission.

Main Flow:

&emsp;1. User navigates to Knowledge Graph view 

&emsp;User clicks a node to view details and related transcripts.

Subflows:

&emsp;5a. User filters through stakeholders 

Alternate Flows:

&emsp;A1. Graph retrieval error → system retries once, then shows error state.

Postconditions:

&emsp;User gains visual understanding of dependencies and ownership.

---

### UC 4: Semantic Chat with AI Assistant

Primary Actor: Project Manager

Preconditions:

&emsp;Transcript vectorization completed (FAISS index built).

Main Flow:

&emsp;1. User navigates to Conversation panel.

&emsp;2. User types a question about a requirement.

&emsp;3. System performs semantic search in FAISS.

&emsp;4. Top-matching segments retrieved.

&emsp;5. LLM generates a response summarizing or clarifying requirement/prompt.

&emsp;6. Response displayed in chat UI.

Subflows:

&emsp;5a. LLM also suggests new draft requirements if missing context detected.

Alternate Flows:

&emsp;A1. FAISS index missing → prompt “Please vectorize transcripts first.”

&emsp;A2. LLM request timeout → display fallback text.

Postconditions:

&emsp;User receives AI-assisted insights or drafted requirement statements.

---

### UC 5: Perform Impact Analysis

Primary Actor: Architect
Preconditions:

&emsp;Dependency edges exist between requirements.

Main Flow:

&emsp;1. User selects a node in the graph.

&emsp;2. System highlights dependent and upstream nodes.

&emsp;3. All impacted requirements and stakeholders are displayed

Subflows:

&emsp;3a. User selects "Clear Graph" to reset nodes and begin new discussion.

Alternate Flows:

&emsp;A1. No dependencies detected → “Independent Requirement” message shown.

Postconditions:

&emsp;User knows what changes would affect downstream work.
