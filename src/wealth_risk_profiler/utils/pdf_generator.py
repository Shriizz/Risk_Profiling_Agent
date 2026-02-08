from fpdf import FPDF
from datetime import datetime
import os
import glob


class RiskProfilePDF(FPDF):
    def __init__(self, version: int = 1):
        super().__init__()
        self.version = version
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Wealth Management Risk Profile', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, f'Version {self.version}', 0, 1, 'C')
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


def delete_old_versions(client_id: str, keep_latest: bool = True):
    """
    Delete old PDF versions for a client
    If keep_latest is True, keeps only the most recent version
    """
    pattern = f'reports/risk_profile_{client_id}_v*.pdf'
    files = sorted(glob.glob(pattern))
    
    if keep_latest and len(files) > 1:
        # Delete all but the most recent
        for old_file in files[:-1]:
            try:
                os.remove(old_file)
                print(f"Deleted old version: {old_file}")
            except Exception as e:
                print(f"Error deleting {old_file}: {e}")


def generate_risk_profile_pdf(
    client_id: str, 
    profile_data: dict,
    version: int = 1,
    keep_only_latest: bool = True
) -> str:
    """
    Generate PDF report from risk profile data with version support
    
    Args:
        client_id: Unique client identifier
        profile_data: Dictionary containing risk profile information
        version: Version number for this report
        keep_only_latest: If True, deletes previous versions
    
    Returns:
        Path to generated PDF file
    """
    
    pdf = RiskProfilePDF(version=version)
    pdf.add_page()
    
    # Set margins to have more space
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    
    # Client Info
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'Client ID: {client_id[:8]}...', 0, 1)
    pdf.ln(5)
    
    # Version Info (if edited)
    if version > 1:
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(200, 0, 0)  # Red for edited versions
        pdf.cell(0, 8, f'Profile Updated - Version {version}', 0, 1)
        pdf.set_text_color(0, 0, 0)  # Reset to black
        pdf.ln(3)
    
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
    
    # Add disclaimer for edited reports
    if version > 1:
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(
            0, 5,
            'Note: This is an updated version of your risk profile. '
            'The analysis has been regenerated based on your corrected information.',
            0, 'C'
        )
    
    # Save PDF with version number
    os.makedirs('reports', exist_ok=True)
    filename = f'reports/risk_profile_{client_id}_v{version}.pdf'
    pdf.output(filename)
    
    # Optionally delete old versions
    if keep_only_latest and version > 1:
        delete_old_versions(client_id, keep_latest=True)
    
    return filename


def get_latest_report_version(client_id: str) -> int:
    """
    Get the version number of the latest report for a client
    Returns 0 if no reports exist
    """
    pattern = f'reports/risk_profile_{client_id}_v*.pdf'
    files = glob.glob(pattern)
    
    if not files:
        return 0
    
    # Extract version numbers from filenames
    versions = []
    for file in files:
        try:
            # Extract version number from filename
            version_str = file.split('_v')[1].split('.pdf')[0]
            versions.append(int(version_str))
        except:
            continue
    
    return max(versions) if versions else 0