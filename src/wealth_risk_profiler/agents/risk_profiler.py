from agno.agent import Agent
from agno.models.ollama import Ollama
import json
from typing import Optional,Tuple
import re

def create_risk_profiling_agent(model: str = "llama3.2"):
    """
    Creates an Agno agent for wealth management risk profiling
    """

    system_prompt = """You are a professional wealth management advisor specializing in client onboarding and risk profiling.

Your goal is to gather the following information through natural conversation:
1. Age and investment timeline (investment horizon in years)
2. Risk tolerance (conservative, moderate, aggressive)
3. Primary investment goals (retirement, wealth_building, income_generation, capital_preservation)
4. Annual income range
5. Existing investment portfolio value

## CONVERSATION FLOW:

### Phase 1: Data Collection
- Ask ONE question at a time
- Be conversational and empathetic
- Provide brief educational context when needed
- Track which fields have been collected

### Phase 2: Review & Confirmation (IMPORTANT)
When you have collected ALL 5 data points:
1. DO NOT generate the final JSON yet
2. Show a formatted summary of collected information
3. Ask: "Does this information look correct? Please review and let me know if you'd like to change anything, or say 'confirm' to proceed."
4. Wait for user response

### Phase 3: Handle User Response
If user says:
- "Yes" / "Confirm" / "Correct" / "Looks good" → Proceed to generate final JSON
- "Edit [field]" / "Change [field]" / "Wrong [field]" → Ask for the correct value
- "Actually [correction]" → Identify what needs to change and ask for confirmation

### Phase 4: Generate Final Profile
Only after user confirms, respond with JSON in this exact format:
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

## EDIT HANDLING:

If at ANY point the user says they made a mistake or wants to edit:
1. Acknowledge their request
2. Ask what the correct value should be
3. Update your understanding
4. Show the updated summary
5. Ask for confirmation again

Examples of edit requests:
- "Actually I'm 30, not 28"
- "Can I change my income?"
- "I meant aggressive risk tolerance"
- "Edit my age to 35"

## RISK SCORING LOGIC:

Calculate risk score based on:
- Age: Younger = higher score (under 30: +20, 30-40: +10, 40-50: 0, 50-60: -10, 60+: -20)
- Horizon: Longer = higher score (25+ years: +20, 15-25: +15, 10-15: +10, 5-10: +5, <5: -10)
- Tolerance: Conservative: -20, Moderate: 0, Aggressive: +20
- Income: Higher = higher score (200k+: +15, 150-200k: +10, 100-150k: +5, <50k: -5)

Final categories:
- Conservative: 1-35 (Age 50+, short horizon, low risk tolerance)
- Moderate: 36-65 (Age 30-50, medium horizon, balanced approach)
- Aggressive: 66-100 (Age <30, long horizon, high risk tolerance)

## PORTFOLIO ALLOCATION:

Based on risk category:
- Conservative: 30% stocks, 50% bonds, 15% cash, 5% alternatives
- Moderate: 60% stocks, 30% bonds, 5% cash, 5% alternatives  
- Aggressive: 80% stocks, 10% bonds, 5% cash, 5% alternatives

## IMPORTANT REMINDERS:

1. ALWAYS show summary and ask for confirmation before generating JSON
2. NEVER skip the review step
3. Be patient with edits - users may change their mind multiple times
4. Keep the conversation friendly and professional
5. Only output the final JSON after explicit confirmation
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
    
def detect_edit_request(user_message: str) -> Optional[Tuple[str, Optional[str]]]:
    """ Detect if an user wants to edit a field.
        Returns: (field_name, new_value) or None
    """
    message_lower = user_message.lower()

    field_keywords = {
        "age" : ["age"],
        "investment_horizon" : ["timeline","horizon","investment timeline","investment horizon"],
        "risk_tolerance" : ["risk","risk tolerance","tolerance"],
        "investment_goal" : ["goal","investment goal"],
        "annual_income" : ["income","salary","annual income"],
        "existing_investments" : ["investments","portfolio","existing investments"]
    }

    edit_triggers = ["edit","change","update","modify","fix","correct","actually","wrong","mistake","meant","should be"]

    if not any(trigger in message_lower for trigger in edit_triggers):
        return None
    
    detected_field = None
    for field, keywords in field_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_field = field
            break
    
    if not detected_field:
        return None
    
    new_value = None

    to_pattern = r'(?:to|is)\s+(\d+(?:\.\d+)?(?:k)?)'
    match = re.search(to_pattern,message_lower)
    if match:
        value_str = match.group(1)

        if 'k' in value_str:
            new_value = str(float(value_str.replace('k',' ')) * 1000)
        else:
            new_value = value_str

    
    if detected_field == "age":
        age_pattern = r"(?:i'm|i am|age is)\s+(\d+)"
        match = re.search(age_pattern,message_lower)
        if match:
            new_value = match.group(1)

    if detected_field == "risk_tolerance":
        if "conservative" in message_lower:
            new_value = "conservative"
        if "moderate" in message_lower:
            new_value = "moderate"        
        if "aggresive" in message_lower:
            new_value = "aggresive"
        
    if detected_field == "investment_goal":
        if "retirement" in message_lower:
            new_value = "retirement"
        if "wealth_buiilding" in message_lower:
            new_value = "wealth_building"
        if "income_generation" in message_lower:
            new_value = "income_generation"
        if "capital_preservation" in message_lower:
            new_value = "capital_preservation"

    return (detected_field, new_value)


def is_confirmation(user_message: str) -> bool:
    """Check if user is confirming the profile"""
    message_lower = user_message.lower().strip()

    confirmation_phrases = ["yes","confirm","correct","all good","looks good","that's right","looks correct","proceed","continue","yes, that's correct","yepp","yeah","yep","sure"]

    return any(phrase in message_lower for phrase in confirmation_phrases)

def calculate_risk_score(age: int,horizon: int,tolerance: str,income: float,existing_inv: float) -> int:
    """Calculate risk score based on multiple factors"""
    score = 50

    if age < 30:
        score += 20
    elif age < 40:
        score += 10
    elif age < 50:
        score += 0
    elif age < 60:
        score -= 10
    else:
        score -= 20

    if horizon >= 25:
        score += 20
    elif horizon >= 15:
        score += 15
    elif horizon >= 10:
        score += 10
    elif horizon >= 5:
        score += 5

    tolerance_map = {
        "conservative" : -20,
        "moderate" : 0,
        "aggresive" : 20
    }
    
    score += tolerance_map.get(tolerance.lower(),0)

    if income >= 200000:
        score += 15
    elif income >= 150000:
        score += 10
    elif income >= 100000:
        score += 5
    elif income < 50000:
        score -= 5

    if existing_inv >= 500000:
        score += 10
    elif existing_inv >= 250000:
        score += 5

    return max(1,min(100,score))