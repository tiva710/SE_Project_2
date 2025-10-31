from fastapi import APIRouter, UploadFile, File
import whisper
import tempfile
import os
from datetime import datetime

# Initialize router (NOT app)
router = APIRouter()

# Load Whisper model
model = whisper.load_model("tiny")

# In-memory store
TRANSCRIPTIONS = []


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes an uploaded audio file and stores the result in memory with a timestamp.
    """
    try:
        # Save uploaded file temporarily
        ext = os.path.splitext(file.filename)[-1] or ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Run Whisper transcription
        result = model.transcribe(tmp_path)
        text = result["text"].strip()

        # Clean up
        os.remove(tmp_path)

        # Store transcription with metadata
        entry = {
            "id": len(TRANSCRIPTIONS) + 1,
            "filename": file.filename,
            "text": text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        TRANSCRIPTIONS.append(entry)

        return {"message": "Transcription successful", "text": text, "entry": entry}

    except Exception as e:
        return {"error": str(e)}


@router.get("/transcriptions")
async def get_all_transcriptions():
    """
    Returns all stored transcriptions for display in the sidebar.
    """
    return {"count": len(TRANSCRIPTIONS), "transcriptions": TRANSCRIPTIONS}
