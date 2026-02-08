# Wealth Risk Profiling Agent - Context Document
Project Overview
This is a wealth management client onboarding chatbot built with FastAPI, Ollama (llama3.2), and modern Python tooling. The agent conducts conversational risk profiling to generate personalized investment recommendations and PDF reports.
Tech Stack

Backend: FastAPI
LLM: Ollama (llama3.2) - local inference
Package Manager: uv
PDF Generation: FPDF2
Python Version: 3.11+

Project Structure
wealth-risk-profiler/
├── src/
│   └── wealth_risk_profiler/
│       ├── __init__.py
│       ├── main.py              # FastAPI application
│       ├── models.py            # Pydantic models
│       ├── agents/
│       │   ├── __init__.py
│       │   └── risk_profiler.py # Agent logic (FOCUS AREA)
│       └── utils/
│           ├── __init__.py
│           └── pdf_generator.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── reports/                     # Generated PDFs
├── pyproject.toml
└── README.md
Risk Profiling Agent - Current Implementation
File: src/wealth_risk_profiler/agents/risk_profiler.py
pythonimport ollama
import json


SYSTEM_PROMPT = """You are a professional wealth management advisor specializing in client onboarding and risk profiling.

Your goal is to gather the following information through natural conversation:
1. Age and investment timeline (investment horizon)
2. Risk tolerance (conservative, moderate, aggressive)
3. Primary investment goals (retirement, wealth building, income, preservation)
4. Annual income range
5. Existing investment portfolio value

Guidelines:
- Ask ONE question at a time
- Be conversational and empathetic
- Provide brief educational context when needed
- After gathering all info, provide a comprehensive risk assessment

When you have all information, respond with JSON in this exact format:
{
    "profile_complete": true,
    "risk_score": 85,
    "risk_category": "aggressive",
    "allocation": {
        "stocks": 80,
        "bonds": 10,
        "cash": 5,
        "alternatives": 5
    },
    "insights": ["insight1", "insight2", "insight3"],
    "next_steps": ["step1", "step2", "step3"]
}

Risk scoring logic:
- Conservative: 1-35 (Age 50+, short horizon, low risk tolerance)
- Moderate: 36-65 (Age 30-50, medium horizon, balanced approach)
- Aggressive: 66-100 (Age <30, long horizon, high risk tolerance)
"""


def get_agent_response(prompt: str, conversation_history: list = None) -> str:
    """Get response from Ollama LLM"""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": prompt})
    
    response = ollama.chat(
        model='llama3.2',
        messages=messages
    )
    
    return response['message']['content']


def extract_profile_data(response_text: str) -> dict:
    """Extract structured data from agent response"""
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
How It's Used in main.py
pythonfrom wealth_risk_profiler.agents.risk_profiler import get_agent_response, extract_profile_data

@app.post("/api/session/start")
async def start_session():
    """Start a new client profiling session"""
    client_id = str(uuid.uuid4())
    sessions[client_id] = ClientProfile(client_id=client_id)

    greeting = get_agent_response(
        "Start a conversation to gather client risk profile information. Greet warmly and ask the first question."
    )

    sessions[client_id].conversation_history.append(
        ChatMessage(role="assistant", content=greeting)
    )

    return {
        "client_id": client_id,
        "message": greeting
    }


@app.post("/api/chat/{client_id}")
async def chat(client_id: str, message: ChatMessage):
    """Continue conversation"""
    
    session = sessions[client_id]
    session.conversation_history.append(message)

    # Build message history for Ollama
    ollama_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in session.conversation_history
    ]

    response_text = get_agent_response(message.content, ollama_messages)

    session.conversation_history.append(
        ChatMessage(role="assistant", content=response_text)
    )

    profile_data = extract_profile_data(response_text)

    if profile_data and profile_data.get("profile_complete"):
        # Generate PDF and return results
        ...
Data Models (models.py)
pythonfrom pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class InvestmentGoal(str, Enum):
    RETIREMENT = "retirement"
    WEALTH_BUILDING = "wealth_building"
    INCOME_GENERATION = "income_generation"
    CAPITAL_PRESERVATION = "capital_preservation"


class ChatMessage(BaseModel):
    role: str = Field(..., description="User or assistant")
    content: str = Field(..., description="Message content")


class ClientProfile(BaseModel):
    client_id: str
    age: Optional[int] = None
    investment_horizon: Optional[int] = None  # years
    risk_tolerance: Optional[RiskTolerance] = None
    investment_goal: Optional[InvestmentGoal] = None
    annual_income: Optional[float] = None
    existing_investments: Optional[float] = None
    conversation_history: List[ChatMessage] = []
```

## Current Agent Behavior

### Example Conversation Flow:
```
Agent: Hello! I'm here to help create your personalized investment profile. 
       Let's start - what's your age?

User: I'm 28 years old

Agent: Great! That's a wonderful age to start building wealth. 
       And what's your investment timeline? How many years are you planning to invest?

User: I'm planning to invest for 30 years

Agent: Excellent long-term horizon! How would you describe your risk tolerance?
       Are you conservative, moderate, or comfortable with aggressive investments?

User: I'm comfortable with high risk for higher returns

... (continues until all 5 data points collected)

Agent: [Provides comprehensive summary with embedded JSON]
{
  "profile_complete": true,
  "risk_score": 87,
  "risk_category": "aggressive",
  "allocation": {
    "stocks": 75,
    "bonds": 10,
    "cash": 5,
    "alternatives": 10
  },
  "insights": [...],
  "next_steps": [...]
}
Known Issues & Limitations

JSON Extraction: Sometimes LLM wraps JSON in markdown code blocks (```json)
Inconsistent Formatting: Agent might not always return exact JSON format
No Memory: Each conversation is stateless (sessions stored in-memory dict)
Hardcoded Model: Currently fixed to llama3.2
No Validation: Doesn't validate user inputs (age ranges, income bounds)
Basic Scoring: Risk score calculation is rule-based, not data-driven

Potential Improvements
1. Multi-Agent Architecture

Information Gatherer Agent: Collects data conversationally
Risk Analyzer Agent: Calculates risk score based on responses
Recommendation Agent: Generates portfolio allocation
Report Generator Agent: Creates insights and next steps

2. Structured Output
python# Use JSON schema enforcement
from pydantic import BaseModel

class RiskProfile(BaseModel):
    profile_complete: bool
    risk_score: int
    risk_category: str
    allocation: dict
    insights: list
    next_steps: list

# Force LLM to output valid JSON
response = ollama.chat(
    model='llama3.2',
    messages=messages,
    format=RiskProfile.model_json_schema()  # Structured output
)
3. Dynamic Risk Scoring
pythondef calculate_risk_score(age: int, horizon: int, tolerance: str, income: float) -> int:
    """Calculate risk score based on multiple factors"""
    score = 50  # baseline
    
    # Age factor (younger = higher score)
    if age < 30:
        score += 20
    elif age < 40:
        score += 10
    elif age > 50:
        score -= 15
    
    # Horizon factor
    if horizon > 20:
        score += 15
    elif horizon > 10:
        score += 5
    
    # Tolerance factor
    tolerance_map = {"conservative": -20, "moderate": 0, "aggressive": 20}
    score += tolerance_map.get(tolerance, 0)
    
    # Income factor (higher income = can take more risk)
    if income > 150000:
        score += 10
    
    return max(1, min(100, score))  # Clamp between 1-100
4. Conversation State Tracking
pythonclass ConversationState(Enum):
    GREETING = "greeting"
    COLLECTING_AGE = "collecting_age"
    COLLECTING_HORIZON = "collecting_horizon"
    COLLECTING_RISK = "collecting_risk"
    COLLECTING_GOAL = "collecting_goal"
    COLLECTING_INCOME = "collecting_income"
    COLLECTING_INVESTMENTS = "collecting_investments"
    ANALYZING = "analyzing"
    COMPLETE = "complete"

# Track progress through conversation
def get_next_question(state: ConversationState) -> str:
    questions = {
        ConversationState.GREETING: "What's your age?",
        ConversationState.COLLECTING_AGE: "What's your investment timeline?",
        # ... etc
    }
    return questions.get(state)
5. Integration with Agno Framework
pythonfrom agno import Agent, Workflow

# Define specialized agents
info_collector = Agent(
    name="Information Collector",
    instructions="Gather client information conversationally",
    model="llama3.2"
)

risk_analyzer = Agent(
    name="Risk Analyzer", 
    instructions="Calculate risk profile from client data",
    model="llama3.2"
)

# Create workflow
profiling_workflow = Workflow(
    agents=[info_collector, risk_analyzer],
    name="Risk Profiling"
)
Testing the Agent
python# Test script
from wealth_risk_profiler.agents.risk_profiler import get_agent_response, extract_profile_data

# Simulate conversation
conversation = []

# First message
response1 = get_agent_response("Hi, I want to create an investment profile")
print(f"Agent: {response1}")

# Continue conversation
conversation.append({"role": "user", "content": "I'm 28 years old"})
response2 = get_agent_response("I'm 28 years old", conversation)
print(f"Agent: {response2}")

# ... continue until complete

# Extract final profile
profile = extract_profile_data(response_final)
print(profile)
Environment Requirements
bash# Install dependencies
uv sync

# Start Ollama
ollama serve

# Pull model
ollama pull llama3.2

# Run API
uv run uvicorn wealth_risk_profiler.main:app --reload
API Endpoints Related to Agent

POST /api/session/start - Initialize conversation
POST /api/chat/{client_id} - Send message to agent
GET /api/profile/{client_id} - Get conversation history

Configuration Options
python# In risk_profiler.py, you can modify:

# 1. Model selection
model='llama3.2'  # Can change to llama3.1, mistral, etc.

# 2. System prompt
SYSTEM_PROMPT = """..."""  # Customize agent behavior

# 3. Risk scoring thresholds
# Conservative: 1-35
# Moderate: 36-65
# Aggressive: 66-100

# 4. Required data points (currently 5)
# Add more: "Employment status", "Dependents", "Debt", etc.
Next Steps for Enhancement

Add conversation validation: Ensure all required fields are collected
Implement retry logic: Handle LLM failures gracefully
Add conversation branching: Different paths based on user responses
Implement memory: Store conversations in database (Redis/PostgreSQL)
Add regulatory compliance: Ensure recommendations meet financial regulations
Implement A/B testing: Test different prompt strategies
Add multilingual support: Support multiple languages
Implement RAG: Use vector database for personalized recommendations based on similar clients

Questions to Address in New Conversation

How to improve JSON extraction reliability?
Should we use function calling instead of JSON in response?
How to handle edge cases (very young/old investors)?
Should we validate responses in real-time?
How to make the conversation more natural?
Should we add confirmation steps before finalizing?
How to handle incomplete conversations (user drops off)?
Should we implement conversation timeouts?


This context document focuses specifically on the Risk Profiling Agent component and its integration within the larger system.