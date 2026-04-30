from fastapi import APIRouter
import config

router = APIRouter()


@router.get("/status")
async def get_status():
    """Return API health status and configuration info."""
    from routers.upload import sessions

    return {
        "status": "ok",
        "api_key_configured": bool(config.GOOGLE_API_KEY),
        "active_sessions": len(sessions),
        "sessions": {
            sid: {
                "status": info.get("status", "unknown"),
                "resume_file": info.get("resume", {}).get("filename", "N/A"),
                "jd_file": info.get("job_description", {}).get("filename", "N/A"),
                "chat_messages": len(info.get("chat_history", []))
            }
            for sid, info in sessions.items()
        }
    }
