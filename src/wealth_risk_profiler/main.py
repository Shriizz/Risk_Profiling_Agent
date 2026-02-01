from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid
import ollama
import json

from wealth_risk_profiler.models import (
    ChatMessage, ClientProfile, RiskProfileResponse, RiskTolerance
)
from wealth_risk_profiler.agents.risk_profiler import (
    create_risk_profiling_agent, extract_profile_data
)
from wealth_risk_profiler.utils.pdf_generator import generate_risk_profile_pdf

app = FastAPI(
    title="Wealth Risk Profiling API",
    description="AI-powered client onboarding and risk assessment",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, ClientProfile] = {}

risk_agent = create_risk_profiling_agent(model="llama3.2")


@app.get("/")
async def root():
    return {
        "message": "Wealth Risk Profiling API",
        "version": "1.0.0",
        "endpoints": {
            "start_session": "/api/session/start",
            "chat": "/api/chat/{client_id}",
            "get_profile": "/api/profile/{client_id}",
            "download_report": "/api/report/{client_id}"
        }
    }


@app.post("/api/session/start")
async def start_session():
    """Start a new client profiling session"""
    client_id = str(uuid.uuid4())
    sessions[client_id] = ClientProfile(client_id=client_id)

    # Correct Agno usage - use print_response=False to get just the content
    greeting = risk_agent.run(
        "Start a conversation to gather client risk profile information. Greet warmly and ask the first question.",
        stream=False
    )

    sessions[client_id].conversation_history.append(
        ChatMessage(role="assistant", content=greeting.content)
    )

    return {
        "client_id": client_id,
        "message": greeting.content
    }


@app.post("/api/chat/{client_id}")
async def chat(client_id: str, message: ChatMessage):
    """Continue conversation with the risk profiling agent"""
    
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[client_id]
    session.conversation_history.append(message)

    # Build conversation context
    conversation_context = "\n".join([
        f"{msg.role}: {msg.content}" 
        for msg in session.conversation_history
    ])

    # Get agent response (synchronous call)
    response = risk_agent.run(
        f"Previous conversation:\n{conversation_context}\n\nUser: {message.content}",
        stream=False
    )

    # DEBUG output
    print("\n" + "="*50)
    print("RAW AGENT RESPONSE:")
    print(response.content)
    print("="*50 + "\n")

    session.conversation_history.append(
        ChatMessage(role="assistant", content=response.content)
    )

    # Extract profile data
    profile_data = extract_profile_data(response.content)

    # DEBUG output
    print("\n" + "="*50)
    print("EXTRACTED PROFILE DATA:")
    print(json.dumps(profile_data, indent=2))
    print("="*50 + "\n")

    if profile_data and profile_data.get("profile_complete"):
        # Add fallback for missing risk_category
        if not profile_data.get("risk_category"):
            risk_score = profile_data.get("risk_score", 50)
            if risk_score <= 35:
                profile_data["risk_category"] = "conservative"
            elif risk_score <= 65:
                profile_data["risk_category"] = "moderate"
            else:
                profile_data["risk_category"] = "aggressive"
        
        try:
            pdf_path = generate_risk_profile_pdf(client_id, profile_data)
            
            return {
                "message": response.content,
                "profile_complete": True,
                "profile_data": profile_data,
                "pdf_url": f"/api/report/{client_id}"
            }
        except Exception as e:
            print(f"PDF generation error: {e}")
            return {
                "message": response.content,
                "profile_complete": True,
                "profile_data": profile_data,
                "error": f"PDF generation failed: {str(e)}"
            }
    
    return {
        "message": response.content,
        "profile_complete": False
    }


@app.get("/api/profile/{client_id}")
async def get_profile(client_id: str):
    """Get current client profile"""
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return sessions[client_id]


@app.get("/api/report/{client_id}")
async def download_report(client_id: str):
    """Download risk profile PDF report"""
    import glob
    
    reports = glob.glob(f'reports/risk_profile_{client_id}_*.pdf')
    
    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    latest_report = max(reports)
    
    return FileResponse(
        path=latest_report,
        media_type='application/pdf',
        filename=f'risk_profile_{client_id}.pdf'
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        ollama.list()
        return {"status": "healthy", "ollama": "connected"}
    except:
        return {"status": "degraded", "ollama": "disconnected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)