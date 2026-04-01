"""
Image Generator - now powered by CrewAI and Gemini Pro
This module wraps the CrewAI flow for backward compatibility
"""
from models import Campaign
from crew_flow import CampaignGenerationFlow


class ImageGenerator:
    """
    Wrapper class for the CrewAI-powered campaign generation flow.
    Maintains API compatibility with the original implementation.
    """
    def __init__(self, storage_root: str = "storage", outputs_root: str = "images"):
        self.storage_root = storage_root
        self.outputs_root = outputs_root
        self.flow = CampaignGenerationFlow(storage_root, outputs_root)

    def extract_details(self, campaign: Campaign, initial_images: list) -> Campaign:
        """
        Deprecated: This method is now part of the CrewAI flow.
        Maintained for backward compatibility.
        """
        # This is now handled in Step 1 of the flow
        return campaign

    def generate_missing(self, campaign: Campaign) -> Campaign:
        """
        Deprecated: This method is now part of the CrewAI flow.
        Maintained for backward compatibility.
        """
        # This is now handled in Step 2 of the flow
        return campaign

    def evaluate_and_plan(self, campaign: Campaign) -> Campaign:
        """
        Deprecated: This method is now part of the CrewAI flow.
        Maintained for backward compatibility.
        """
        # This is now handled in Step 3 of the flow
        return campaign

    def process_campaign(self, campaign: Campaign) -> Campaign:
        """
        Main entry point: Execute the complete CrewAI flow.
        This replaces the need to call extract_details, generate_missing, and evaluate_and_plan separately.
        """
        return self.flow.execute(campaign)
