import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from services import document_processor, vector_store
import config

router = APIRouter()

# In-memory session store
sessions = {}


@router.post("/upload")
async def upload_files(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...)
):
    """
    Upload resume and job description files.
    Extracts text, chunks it, and stores embeddings in ChromaDB.
    Returns a session ID for subsequent API calls.
    """
    # Validate file types
    allowed_extensions = {".pdf", ".txt"}

    for file_obj, label in [(resume, "resume"), (job_description, "job_description")]:
        ext = os.path.splitext(file_obj.filename or "")[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {label} file type: '{ext}'. Only PDF and TXT files are allowed."
            )

    # Generate session ID
    session_id = str(uuid.uuid4())[:8]
    session_dir = os.path.join(config.UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    results = {}

    try:
        for file_obj, label in [(resume, "resume"), (job_description, "job_description")]:
            # Save file
            file_path = os.path.join(session_dir, f"{label}{os.path.splitext(file_obj.filename or '')[1].lower()}")
            content = await file_obj.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Extract and clean text
            text = document_processor.extract_text(file_path)
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not extract any text from the {label} file. Please check the file."
                )

            cleaned = document_processor.clean_text(text)

            # Chunk text
            chunks = document_processor.chunk_text(cleaned, chunk_size=500, chunk_overlap=50)

            # Store embeddings
            collection_name = f"{session_id}_{label}"
            num_stored = vector_store.store_embeddings(
                chunks=chunks,
                collection_name=collection_name,
                source_type=label
            )

            results[label] = {
                "filename": file_obj.filename,
                "text_length": len(cleaned),
                "num_chunks": len(chunks),
                "chunks_stored": num_stored
            }

        # Store session info
        sessions[session_id] = {
            "status": "uploaded",
            "resume": results.get("resume", {}),
            "job_description": results.get("job_description", {}),
            "analysis": None,
            "chat_history": []
        }

        return {
            "success": True,
            "session_id": session_id,
            "message": "Files uploaded and processed successfully",
            "details": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")
