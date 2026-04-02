"""
Image Generator - now powered by CrewAI and Gemini Pro
This module wraps the CrewAI flow for backward compatibility
"""
from src.database import Database
from src.models import Campaign
from src.flows.crew_flow import CampaignGenerationFlow


class ImageGenerator:
    """
    Wrapper class for the CrewAI-powered campaign generation flow.
    Maintains API compatibility with the original implementation.
    """
    def __init__(self):
        self.flow = CampaignGenerationFlow("storage")

    def process_campaign(self, campaign: Campaign) -> Campaign:
        """
        Main entry point: Execute the complete CrewAI flow.
        This replaces the need to call extract_details, generate_missing, and evaluate_and_plan separately.
        """
        return self.flow.execute(campaign)
