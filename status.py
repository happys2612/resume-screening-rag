from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import rag_engine, vector_store

router = APIRouter()


class AnalyzeRequest(BaseModel):
    session_id: str


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Analyze the match between uploaded resume and job description.
    Uses RAG to retrieve relevant chunks before sending to Gemini.
    """
    session_id = request.session_id

    # Verify collections exist
    resume_collection = f"{session_id}_resume"
    jd_collection = f"{session_id}_job_description"

    if not vector_store.collection_exists(resume_collection):
        raise HTTPException(
            status_code=404,
            detail="Resume data not found. Please upload files first."
        )

    if not vector_store.collection_exists(jd_collection):
        raise HTTPException(
            status_code=404,
            detail="Job description data not found. Please upload files first."
        )

    try:
        result = rag_engine.analyze_match(session_id)

        # Update session if it exists in upload module
        from routers.upload import sessions
        if session_id in sessions:
            sessions[session_id]["status"] = "analyzed"
            sessions[session_id]["analysis"] = result

        return {
            "success": True,
            "session_id": session_id,
            "analysis": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
