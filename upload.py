from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from services import rag_engine, vector_store

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    chat_history: Optional[List[Dict]] = None


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    RAG-based conversational chat over resume and JD content.
    Retrieves relevant chunks based on user question before responding.
    """
    session_id = request.session_id

    # Verify resume collection exists
    resume_collection = f"{session_id}_resume"
    if not vector_store.collection_exists(resume_collection):
        raise HTTPException(
            status_code=404,
            detail="No uploaded documents found. Please upload files first."
        )

    try:
        result = rag_engine.chat(
            question=request.message,
            session_id=session_id,
            chat_history=request.chat_history
        )

        # Update chat history in session
        from routers.upload import sessions
        if session_id in sessions:
            if sessions[session_id]["chat_history"] is None:
                sessions[session_id]["chat_history"] = []
            sessions[session_id]["chat_history"].append(
                {"role": "user", "content": request.message}
            )
            sessions[session_id]["chat_history"].append(
                {"role": "assistant", "content": result["answer"]}
            )

        return {
            "success": True,
            "response": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
