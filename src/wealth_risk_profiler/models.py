from pydantic import BaseModel, Field
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


class RiskProfileResponse(BaseModel):
    risk_score: int = Field(..., ge=1, le=100)
    risk_category: RiskTolerance
    recommended_allocation: dict
    key_insights: List[str]
    next_steps: List[str]
    pdf_url: Optional[str] = None