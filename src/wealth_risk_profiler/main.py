from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid
import ollama
import json

from wealth_risk_profiler.models import (
    ChatMessage, ClientProfile, RiskProfileResponse, RiskTolerance,ProfileStatus
)
from wealth_risk_profiler.agents.risk_profiler import (
    create_risk_profiling_agent, extract_profile_data,detect_edit_request,is_confirmation
)
from wealth_risk_profiler.utils.pdf_generator import generate_risk_profile_pdf,get_latest_report_version

app = FastAPI(
    title="Wealth Risk Profiling API",
    description="AI-powered client onboarding and risk assessment-now with edit support",
    version="1.0.1"
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
        "version": "1.0.1",
        "features" : ["Review and confirm before PDF Generation","Edit profile fields at any time","PDF Versioning support","Enhanced conversation flow"],
        "endpoints": {
            "start_session": "/api/session/start",
            "chat": "/api/chat/{client_id}",
            "get_profile": "/api/profile/{client_id}",
            "update_field" : "/api/profile/{client_id}/update",
            "regenerate" : "/api/profile/{client_id}/regenerate",
            "download_report": "/api/report/{client_id}"
        }
    }


@app.post("/api/session/start")
async def start_session():
    """Start a new client profiling session"""
    client_id = str(uuid.uuid4())
    sessions[client_id] = ClientProfile(client_id=client_id,profile_status=ProfileStatus.COLLECTING)

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
        "message": greeting.content,
        "status" : sessions[client_id].profile_status.value,
        "profile_version" : sessions[client_id].profile_version
    }


@app.post("/api/chat/{client_id}")
async def chat(client_id: str, message: ChatMessage):
    """Continue conversation with the risk profiling agent, Handles: data collection, review, confirmation, and edits"""
    
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[client_id]
    session.conversation_history.append(message)

    if session.profile_status == ProfileStatus.REVIEWING and is_confirmation(message.content):
        session.profile_status = ProfileStatus.CONFIRMED

    # Build conversation context
    conversation_context = "\n".join([
        f"{msg.role}: {msg.content}" 
        for msg in session.conversation_history
    ])

    # Get agent response (synchronous call)
    response = risk_agent.run(
            f"Previous conversation:\n{conversation_context}\n\n"
            f"User has confirmed the profile. Generate the final JSON response now.",
        stream=False
    )


    session.conversation_history.append(ChatMessage(role="assistant",content=response.content))

    profile_data = extract_profile_data(response.content)

    if profile_data and profile_data.get("profile_complete"):
        if not profile_data.get("risk_category"):
            risk_score = profile_data.get("risk_score",50)
            if risk_score <= 35:
                profile_data["risk_category"] = "conservative"
            elif risk_score <= 65 :
                profile_data["risk_category"] = "moderate"
            else:
                profile_data["risk_category"] = "aggressive"
        
        try:
            pdf_path = generate_risk_profile_pdf(
                client_id,
                profile_data,
                version=session.profile_version,
                keep_only_latest=True
            )

            session.profile_status = ProfileStatus.COMPLETE
            session.last_generated_report = pdf_path

            return {
                "message" : response.content,
                "profile_complete" : True,
                "profile_data" : profile_data,
                "pdf_url" : f"/api/report/{client_id}",
                "profile_version" : session.profile_version,
                "status" : session.profile_status.value
            }

        except Exception as e:
            print(f"PDF Generation Error: {e}")
            return {
                "message" : response.content,
                "profile_complete" : True,
                "profile_data" : profile_data,
                "error" : f"PDF generation failed: {str(e)}",
                "status" : session.profile_status.value
            }
    
    edit_request = detect_edit_request(message.content)

    if edit_request:
        field_name,new_value = edit_request
        session.profile_status = ProfileStatus.EDITING

        if new_value:
            try:
                success = session.update_field(field_name,new_value)
                if success:
                    response = risk_agent.run(
                        f"The user has updated their {field_name.replace('_',' ')} to {new_value}."
                        f"Acknowledge this change and show the updated profile summary."
                        f"Then ask if everything looks correct now.",
                        stream=False
                    )

                session.profile_status = ProfileStatus.REVIEWING
                session.conversation_history.append(ChatMessage(role="assistant",content=response.content))

                return {
                    "message" : response.content,
                    "profile_complete" : False,
                    "status" : session.profile_status.value,
                    "updated_field" : field_name,
                    "profile_summary" : session.to_summary_dict()
                }
            except Exception as e:
                return {
                    "message" : f"Sorry, I could not update {field_name}. Could you rephrase that?",
                    "error" : str(e),
                    "status" : session.profile_status.value
                }
        else:
            response = risk_agent.run(f"User wants to edit {field_name.replace('_',' ')}."
                                      f"Ask them what the correct value should be.",
                                      stream=False)

            session.conversation_history.append(ChatMessage(role="assistant",content=response.content))

            return {
                "message" : response.content,
                "profile_complete" : False,
                "status" : session.profile_status.value,
                "editing_field" : field_name
            }

    conversation_context = "\n".join([f"{msg.role}: {msg.content}"
                                      for msg in session.conversation_history])

    response = risk_agent.run(f"Previous conversation: \n {conversation_context} \n\nUser: {message.content}",
                              stream=False)
    

    # DEBUG output
    print("\n" + "="*50)
    print("RAW AGENT RESPONSE:")
    print(response.content)
    print("="*50 + "\n")

    session.conversation_history.append(
        ChatMessage(role="assistant", content=response.content)
    )

    if session.is_complete() and session.profile_status == ProfileStatus.COLLECTING:
        session.profile_status = ProfileStatus.REVIEWING
        print(f"Profile Complete! Moving to REviewing State")


    profile_data = extract_profile_data(response.content)

    if profile_data and profile_data.get("profile_complete"):
        print(f"WARNINGIG: Agent generated JSON before confirmation!!")

    return {
        "message" : response.content,
        "profile_complete" : False,
        "status" : session.profile_status.value,
        "profile_summary" : session.to_summary_dict() if session.is_complete() else None
    }

@app.get("/api/profile/{client_id}")
async def get_profile(client_id: str):
    """Get current client profile with status"""
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[client_id]


    return {
        "client_id" : client_id,
        "profile_data" : session.to_summary_dict(),
        "is_complete" : session.is_complete(),
        "missing_fields" : session.get_missing_fields(),
        "status" : session.profile_status.value,
        "profile_version" : session.profile_version,
        "last_report" : session.last_generated_report,
        "created_at" : session.created_at,
        "updated_at" : session.updated_at
    }


@app.get("/api/profile/{client_id}/update")
async def update_profile_field(client_id: str,field: str,value: str):
    """
    Directly update a specific profile field
    """
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[client_id]

    try:
        success = session.update_field(field,value)

        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid field: {field}. Valid fields: age, investment_horizon, "
                       f"risk_tolerance, investment_goal, annual_income, existing_investments"
            )
    
        if session.profile_status == ProfileStatus.COMPLETE:
            session.profile_version += 1
            session.profile_status = ProfileStatus.EDITING

        return {
            "message" : f"Successfully Updated {field}",
            "profile_summary" : session.to_summary_dict(),
            "profile_version" : session.profile_version,
            "status" : session.profile_status.value
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid value for {field}: {str(e)}"
        )



@app.get("/api/report/{client_id}/regenerate")
async def regenerate_profile(client_id: str):
    """Regenerate risk profile and PDF after edits"""
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[client_id]

    if not session.is_complete():
        raise HTTPException(status_code=400,detail=f"Profile incomplete. Missing fields: {', '.join(session.get_missing_fields())}")
    
    profile_request = """
    Generate a new risk profile for this client:
    Age: {session.age}
    Investment Horizon: {session.investment_horizon} years
    Risk Tolerance: {session.risk_tolerance.value}
    Investment Goal: {session.investment_goal.value}
    Annual Income: ${session.annual_income:,.0f}
    Existing Investments: ${session.existing_investments:,.0f}
    
    Generate the complete JSON response.
    """

    response = risk_agent.run(profile_request,stream=False)

    profile_data = extract_profile_data(response.content)

    if not profile_data or not profile_data.get("profile_complete"):
        raise HTTPException(
            status_code=500,
            detail="Failed to generate profile data"
        )

    if not profile_data.get("profile_complete"):
        risk_score = profile_data.get("risk_score",50)
        if risk_score <= 35:
            profile_data["risk_category"] = "conservative"
        elif risk_score <= 65 :
            profile_data["risk_category"] = "moderate"
        else:
            profile_data["risk_category"] = "aggressive"
    
    try:
        session.profile_version += 1

        pdf_path = generate_risk_profile_pdf(
            client_id,
            profile_data,
            version=session.profile_version,
            keep_only_latest=True
        )

        session.last_generated_report = pdf_path
        session.profile_status = ProfileStatus.COMPLETE

        return {
            "message" : "Profile regenerated successfullyyyy!!",
            "profile_data" : profile_data,
            "profile_version" : session.profile_version,
            "pdf_url" : f"/api/report/{client_id}",
            "status" : session.profile_status.value
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@app.get("/api/report/{client_id}")
async def download_report(client_id: str):
    """Download risk profile PDF report"""
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[client_id]
    
    if not session.last_generated_report:
        raise HTTPException(status_code=404,detail="No Report Generated Yet")
    
    if not session.last_generated_report or not os.path.exists(session.last_generated_report):
        raise HTTPException(status_code=404,detail="Report File Not Found")

    return FileResponse(
        path=session.last_generated_report,
        media_type='application/pdf',
        filename=f'risk_profile_{client_id}_v{session.profile_version}.pdf'
    )

@app.delete("/api/session/{client_id}")
async def delete_session(client_id: str):
    """Delete the session and its associated data"""
    if client_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    del sessions[client_id]

    return {"message" : "Session deleted successfully!!!"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        ollama.list()
        return {"status": "healthy", "ollama": "connected","active_sessions": len(sessions)}
    except:
        return {"status": "degraded", "ollama": "disconnected","active_sessions": len(sessions)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)