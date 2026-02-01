from fpdf import FPDF
from datetime import datetime
import os


class RiskProfilePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Wealth Management Risk Profile', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')


def clean_text(text: str) -> str:
    """Clean text to remove problematic characters and limit length"""
    if not text:
        return ""
    
    # Convert to string and remove non-ASCII characters
    text = str(text).encode('ascii', 'ignore').decode('ascii')
    
    # Remove markdown formatting
    text = text.replace('**', '').replace('*', '').replace('`', '')
    
    # Limit length to prevent overflow
    max_length = 500
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()


def generate_risk_profile_pdf(client_id: str, profile_data: dict) -> str:
    """Generate PDF report from risk profile data"""
    
    pdf = RiskProfilePDF()
    pdf.add_page()
    
    # Set margins to have more space
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    
    # Client Info
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'Client ID: {client_id[:8]}...', 0, 1)
    pdf.ln(5)
    
    # Risk Assessment
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Risk Assessment', 0, 1)
    pdf.set_font('Arial', '', 11)
    
    # Safe access with defaults
    risk_score = profile_data.get("risk_score", "N/A")
    risk_category = profile_data.get("risk_category", "unknown")
    
    pdf.cell(0, 8, f'Risk Score: {risk_score}/100', 0, 1)
    pdf.cell(0, 8, f'Risk Category: {str(risk_category).upper()}', 0, 1)
    pdf.ln(5)
    
    # Recommended Allocation
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Recommended Portfolio Allocation', 0, 1)
    pdf.set_font('Arial', '', 11)
    
    allocation = profile_data.get("allocation", {})
    if allocation:
        for asset, percentage in allocation.items():
            asset_text = f'{str(asset).capitalize()}: {percentage}%'
            pdf.cell(0, 8, asset_text, 0, 1)
    else:
        pdf.cell(0, 8, 'Allocation data not available', 0, 1)
    pdf.ln(5)
    
    # Key Insights
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Key Insights', 0, 1)
    pdf.set_font('Arial', '', 10)  # Smaller font for long text
    
    insights = profile_data.get("insights", [])
    if insights:
        for i, insight in enumerate(insights, 1):
            # Clean and wrap text
            clean_insight = clean_text(insight)
            
            # Use multi_cell with proper width
            pdf.set_x(15)  # Reset X position
            pdf.multi_cell(0, 6, f'{i}. {clean_insight}', 0)
            pdf.ln(2)
    else:
        pdf.cell(0, 8, 'No insights available', 0, 1)
    pdf.ln(3)
    
    # Next Steps
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Recommended Next Steps', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    next_steps = profile_data.get("next_steps", [])
    if next_steps:
        for i, step in enumerate(next_steps, 1):
            # Clean and wrap text
            clean_step = clean_text(step)
            
            # Use multi_cell with proper width
            pdf.set_x(15)  # Reset X position
            pdf.multi_cell(0, 6, f'{i}. {clean_step}', 0)
            pdf.ln(2)
    else:
        pdf.cell(0, 8, 'No next steps available', 0, 1)
    
    # Save PDF
    os.makedirs('reports', exist_ok=True)
    filename = f'reports/risk_profile_{client_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    pdf.output(filename)
    
    return filename