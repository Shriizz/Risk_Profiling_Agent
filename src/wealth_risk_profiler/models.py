from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

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
    timestamp: datetime = Field(default_factory=datetime.now)


class ProfileStatus(str, Enum):
    """Track the status of profile completion"""
    COLLECTING = "collecting" # Still gathering information
    REVIEWING = "reviewing"
    CONFIRMED = "confirmed"  # User confirmed, ready for PDF
    COMPLETE = "COMPLETE"    # PDF generated
    EDITING = "EDITING" # User requested changes

class ClientProfile(BaseModel):
    client_id: str
    age: Optional[int] = None
    investment_horizon: Optional[int] = None  # years
    risk_tolerance: Optional[RiskTolerance] = None
    investment_goal: Optional[InvestmentGoal] = None
    annual_income: Optional[float] = None
    existing_investments: Optional[float] = None
    conversation_history: List[ChatMessage] = []

    profile_status: ProfileStatus = ProfileStatus.COLLECTING
    profile_version: int = 1
    last_generated_report: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def is_complete(self) -> bool:
        """Check if all fields are captured"""
        return all([
            self.age is not None,
            self.investment_horizon is not None,
            self.risk_tolerance is not None,
            self.investment_goal is not None,
            self.annual_income is not None,
            self.existing_investments is not None
        ])
    
    def get_missing_fields(self) -> List[str]:
        """ Return list of fields that are still None"""
        missing = []
        field_map = {
            "age" : self.age,
            "invest_horizon" : self.investment_horizon,
            "risk_tolerance" : self.risk_tolerance,
            "investment_goal" : self.investment_goal,
            "annual_income" : self.annual_income,
            "existing_investments" : self.existing_investments
        }

        return [field for field,value in field_map.items() if value is None]
    
    def to_summary_dict(self) -> Dict[str,str]:
        """Convert profile to human-readable summary for confirmation"""
        return {
            "Age" : str(self.age) if self.age else "Not Provided",
            "Investment Horizon" : f"{self.investment_horizon} years" if self.investment_horizon else "Not Provided",
            "Risk Tolerance" :  self.risk_tolerance.value.title() if self.risk_tolerance else "Not Provided",
            "Investment Goal" : self.investment_goal.value.replace('_',' ').title() if self.investment_goal else "Not Provided",
            "Annual Income" : f"{self.annual_income:.0f}" if self.annual_income else "Not Provided",
            "Existing Investments" : f"{self.existing_investments:,.0f}" if self.existing_investments else "Not Provided"
            }
    
    def to_summary_text(self) -> str:
        """Format profile summary as text for agent to show user"""
        summary_dict = self.to_summary_dict()
        lines = ["📋 **Your Investment Profile Summary:**\n"]
        for key,value in summary_dict.items():
            lines.append(f"• **{key}:** {value}")
        return "\n".join(lines)
    
    def update_field(self,field_name: str,value) -> bool:
        """
        Update a specific field from the Client Profile
        Returns True if successful, False if it doesnt_exist
        """

        field_mapping = {
            "age": "age",
            "timeline": "investment_horizon",
            "horizon": "investment_horizon",
            "investment timeline": "investment_horizon",
            "investment horizon": "investment_horizon",
            "risk": "risk_tolerance",
            "risk tolerance": "risk_tolerance",
            "tolerance": "risk_tolerance",
            "goal": "investment_goal",
            "investment goal": "investment_goal",
            "income": "annual_income",
            "salary": "annual_income",
            "annual income": "annual_income",
            "investments": "existing_investments",
            "portfolio": "existing_investments",
            "existing investments": "existing_investments"
        }


        actual_field = field_mapping.get(field_name.lower(),field_name)

        if hasattr(self,actual_field):
            if actual_field in ["age","investment_horizon"]:
                value = int(value) if isinstance(value, str) else value
            elif actual_field in ["annual_income","existing_investments"]:
                value = float(value) if isinstance(value, str) else value
            elif actual_field == "risk_tolerance":
                value = RiskTolerance(value.lower()) if isinstance(value, str) else value
            elif actual_field == "investment_goal":
                value = InvestmentGoal(value.lower()) if isinstance(value, str) else value

            setattr(self,actual_field,value)
            self.updated_at = datetime.now()

            return True
        return False
    
class RiskProfileResponse(BaseModel):
    risk_score: int = Field(..., ge=1, le=100)
    risk_category: RiskTolerance
    recommended_allocation: dict
    key_insights: List[str]
    next_steps: List[str]
    pdf_url: Optional[str] = None
    profile_version: int = 1