# ReqTrace Graph Backend — API Reference

This document summarizes the HTTP API exposed by the backend. It lists endpoints, methods, expected request parameters and bodies, and response shapes.

---

## Root

- GET /

Description: Basic health message indicating the API is running.

Response (200):
```json
{ "message": "ReqTrace Graph Backend API is running!" }
```

---

## Health

- GET /health

Description: lightweight health check endpoint.

Response (200):
```json
{ "status": "OK" }
```

---

## Transcription / FAISS

### POST /transcribe

Description: Upload an audio file. The server transcribes it with Whisper, runs NER to extract entities/relationships, writes results to Neo4j (idempotent), indexes transcription into FAISS, and returns the generated conversation/recording id and graph data.

Request:
- Content-Type: multipart/form-data
- Form field: `file` — audio file (UploadFile). Example: `file=@meeting.mp3`

Successful Response (200):
```json
{
  "message": "✅ Transcription successful for meeting.mp3",
  "audio_id": "<sha256-hash>",
  "conversation_id": "rec_<hex>",
  "graph_data": {
    "nodes": [ { "id": "feature.checkout_rec_<hex>", "label": "Feature", "props": { ... } }, ... ],
    "links": [ { "type": "depends_on", "source": "...", "target": "...", "props": { ... } }, ... ]
  },
  "entry": {
    "id": 1,
    "conversation_id": "rec_<hex>",
    "audio_id": "<sha256-hash>",
    "filename": "meeting.mp3",
    "text": "transcribed text...",
    "timestamp": "2025-11-06 12:34:56",
    "ner": { "entities": [...], "relationships": [...] },
    "neo4j_write": { ... }
  }
}
```

Error Response (400/500):
```json
{ "error": "❌ Transcription failed: <message>" }
```

Notes:
- Duplicate audio is detected using an audio content hash (`audio_id`). When duplicate, the response includes `skipped: true` and returns the existing `conversation_id` and `graph_data`.
- The NER output contains `entities` and `relationships` arrays; both are tagged with `recording_id` and `audio_id` when stored.

---

### GET /transcriptions

Description: Return all transcriptions kept in an in-memory list during the process lifetime.

Response (200):
```json
{ "count": <int>, "transcriptions": [ { <entry> }, ... ] }
```

---

### GET /search

Description: Search transcription index (FAISS) for similar transcript fragments.

Query Parameters:
- `q` (string, required): search query text
- `top_k` (int, optional, default=3): number of similar results to return

Response (200):
```json
{ "query": "payment fails", "results": [ { "id": ..., "text": "...", "score": 0.83 }, ... ] }
```

Error Response:
```json
{ "error": "Search failed: <message>" }
```

---

### POST /rebuild

Description: Rebuild the FAISS index from in-memory transcriptions. Useful during development.

Response (200):
```json
{ "message": "✅ Rebuilt FAISS index with <n> entries" }
```

Error (500):
```json
{ "error": "❌ Rebuild failed: <message>" }
```

---

## Conversation / Chat

### POST /chat

Description: Accepts a JSON body with a `query` string, uses FAISS to fetch context chunks, then calls OpenAI Chat Completions to answer using the context.

Request Body (application/json):
```json
{ "query": "How do stakeholders affect checkout?" }
```

Response (200):
```json
{
  "query": "How do stakeholders affect checkout?",
  "answer": "<generated answer>",
  "context_used": [ {"id": ..., "text": "...", "score": ...}, ... ]
}
```

Errors:
- 400 when `query` is missing.
- 500 on internal failure; full stack is printed to server logs and HTTP 500 returned with the error string.

Notes:
- The endpoint uses the `openai` client from the OpenAI SDK and requires `OPENAI_API_KEY` present in `.env`.
- The model used in code is `gpt-4o-mini` (update as needed).

---

## Graph endpoints

All graph endpoints are under `/api/graph` and return `GraphResponse` JSON objects with structure `{ "nodes": [Node], "links": [Link] }` where `Node` is `{id, label, props}` and `Link` is `{type, source, target, props}`.

### GET /api/graph/all

Description: Fetch all nodes and relationships across the entire graph database.
Query parameters:
- `limit` (int, optional, default=5000)

Response (200): GraphResponse

### GET /api/graph/stakeholders/overview

Description: Overview subgraph for nodes with label `Stakeholder`.
Query parameters:
- `limit` (int, optional, default=200)

Response (200): GraphResponse

### GET /api/graph/features/overview

Description: Overview for nodes labeled `Feature`.
Query parameters:
- `limit` (int, optional, default=200)

Response (200): GraphResponse

### GET /api/graph/stakeholders/neighborhood

Description: Neighborhood subgraph centered on a stakeholder node id.
Query parameters:
- `id` (string, required): center node id (example: `stakeholder.pm`)
- `k` (int, default=1): number of hops
- `limit` (int, default=500)

Responses:
- 200: GraphResponse
- 404: { "detail": "No nodes found around id=<id>" }

### GET /api/graph/features/neighborhood

Same as stakeholders/neighborhood but with label `Feature`.

### GET /api/graph/conversation/{conversation_id}

Path parameter:
- `conversation_id` (string): conversation/recording ID (e.g., `rec_<hex>`)
Query params:
- `limit` (int, default=2000)

Responses:
- 200: GraphResponse scoped to records with `recording_id` equal to the provided `conversation_id`.
- 404: { "detail": "No nodes found for conversation <conversation_id>" }

---

## Models / Schemas (summary)

- Node
```json
{ "id": "string", "label": "string", "props": { "key": "value", ... } }
```

- Link
```json
{ "type": "string", "source": "string", "target": "string", "props": { ... } }
```

- GraphResponse
```json
{ "nodes": [Node], "links": [Link] }
```

---

## Notes & caveats
- Many endpoints perform network or heavy CPU work (Whisper, OpenAI, Neo4j, FAISS). Use asynchronous client calls and timeouts in production.
- `/transcribe` uses `whisper` model (currently loads `tiny`), which is memory/CPU intensive; consider running OCR/Transcription as a background job.
- `/chat` requires a valid `OPENAI_API_KEY` set in the `.env` file.

If you want, I can:
- Add examples for each request using curl and HTTPie
- Export this API to `docs/API.md` in repo root or generate an OpenAPI YAML file and commit it
- Generate a Postman collection or an OpenAPI-based `swagger.yaml`

---

## Examples (curl & HTTPie)

Below are practical examples you can run against a running server on http://localhost:8000.

1) Transcribe an audio file (curl):

```bash
curl -X POST "http://localhost:8000/transcribe" -F "file=@/path/to/meeting.mp3"
```

1b) Transcribe (HTTPie):

```bash
http --form POST http://localhost:8000/transcribe file@/path/to/meeting.mp3
```

Example response (success):

```json
{
  "message": "✅ Transcription successful for meeting.mp3",
  "audio_id": "<sha256-hash>",
  "conversation_id": "rec_<hex>",
  "graph_data": {"nodes": [...], "links": [...]},
  "entry": { ... }
}
```

2) List transcriptions:

```bash
curl http://localhost:8000/transcriptions
# or
http GET http://localhost:8000/transcriptions
```

3) Search transcripts:

```bash
curl "http://localhost:8000/search?q=payment+fails&top_k=5"
# or
http GET http://localhost:8000/search q=="payment fails" top_k==5
```

4) Rebuild FAISS index:

```bash
curl -X POST http://localhost:8000/rebuild
# or
http POST http://localhost:8000/rebuild
```

5) Chat with context:

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"query":"How do stakeholders affect checkout?"}'
# or
http POST http://localhost:8000/chat query="How do stakeholders affect checkout?"
```

6) Graph endpoints (examples):

```bash
# Fetch all graph
curl "http://localhost:8000/api/graph/all?limit=1000"

# Fetch stakeholder neighborhood
curl "http://localhost:8000/api/graph/stakeholders/neighborhood?id=stakeholder.pm&k=2&limit=500"
```

## OpenAPI YAML — what it gives you and how to generate/use it

What you can do with an OpenAPI YAML file
- Generate client SDKs (TypeScript, Python, Java, etc.) using OpenAPI Generator or `openapi-generator`.
- Import into tools like Postman or Insomnia to run and explore the API.
- Serve interactive docs (Swagger UI / ReDoc) or host the spec at a known URL for integrations.

How to get/generate the OpenAPI YAML from this app
- FastAPI exposes OpenAPI JSON at `/openapi.json` and interactive docs at `/docs` by default.
- This project now provides `/openapi.yaml` (if PyYAML/PyYAML is installed) which returns the YAML representation. If your running environment doesn't have PyYAML, run:

```bash
pip install PyYAML
```

Then fetch the YAML:

```bash
curl http://localhost:8000/openapi.yaml -o openapi.yaml
```

Using the YAML
- Generate clients with OpenAPI Generator:

```bash
# install openapi-generator or use docker
openapi-generator-cli generate -i openapi.yaml -g python -o ./client-python
```

- Import into Postman: `File -> Import -> Upload openapi.yaml`.
- Serve Swagger UI locally from the YAML using `swagger-ui` or `redoc-cli`:

```bash
npx redoc-cli serve openapi.yaml
# or
npx swagger-ui-dist openapi.yaml
```
