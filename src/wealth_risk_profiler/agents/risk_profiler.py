from agno.agent import Agent
from agno.models.ollama import Ollama
import json
from typing import Optional

def create_risk_profiling_agent(model: str = "llama3.2"):
    """
    Creates an Agno agent for wealth management risk profiling
    """

    system_prompt = """ You are a professional wealth management advisor specializing in client onboarding and risk profiling.

    Your goal is to gather the following information through natural conversation:
    1. Age and investment timeline (investment horizon)
    2. Risk Tolerance (conservative,moderate,aggresive)
    3. Primary investment goals (retirement,wealth building,income, preservation)
    4. Annual Income range
    5. Existing investments portfolio value

    Guidelines:
    - Ask ONE question at a time
    - Be conversational and empathetic
    - Provide brief educational context when needed
    - After gathering all info, provide a comprehensive risk assessment
    
    When you have all information, respond with JSON in this exact format:
    {
    "profile_complete": true,
    "risk_score": <1-100>,
    "risk_category": "<conservative|moderate|aggressive>",
    "allocation": {
        "stocks": <percentage>,
        "bonds": <percentage>,
        "cash": <percentage>,
        "alternatives": <percentage>
    },
    "insights": ["insight1", "insight2", "insight3"],
    "next_steps": ["step1", "step2", "step3"]
    }

    Risk scoring logic:
    - Conservative: 1-35 (Age 50+, short horizon, low risk tolerance)
    - Moderate: 36-65 (Age 30-50, medium horizon, balanced approach)
    - Aggressive: 66-100 (Age <30, long horizon, high risk tolerance)

    Portfolio allocation rules:
    - Conservative: 30% stocks, 50% bonds, 15% cash, 5% alternatives
    - Moderate: 60% stocks, 30% bonds, 5% cash, 5% alternatives  
    - Aggressive: 80% stocks, 10% bonds, 5% cash, 5% alternatives
    """

    agent =  Agent(
        name="Wealth Risk Profiler",
        model=Ollama(id=model),
        instructions=system_prompt,
        markdown=True
    )
    
    return agent

def extract_profile_data(response_text: str) -> Optional[dict]:
    """ Extract structured data from agent response"""
    try:
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        return None
    
    except Exception as e:
        print(f"Error extracting profile data: {e}")
        return None