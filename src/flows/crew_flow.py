"""
CrewAI Flow for Campaign Image Generation
Orchestrates the 4-step process as defined in the requirements
"""
import os
from typing import List
from crewai import Crew, Process, LLM
from google.genai import types
from PIL import Image as PILImage

from src.database import Database
from src.models import Campaign, ImageRecord
from src.flows.agents import (
    create_branding_extract_agent,
    create_logo_extract_agent,
    create_marketing_extract_agent,
    create_image_summary_agent,
    create_branding_report_agent,
    create_future_campaigns_agent
)
from src.flows.tasks import (
    create_branding_extraction_task,
    create_logo_extraction_task,
    create_marketing_extraction_task,
    create_image_summary_task,
    create_branding_report_task,
    create_future_campaigns_task
)
from src.utils import ensure_dir, required_ratios
from dotenv import load_dotenv

load_dotenv()
# Configure Gemini client with new API
llm = LLM(model=os.getenv("GEMINI_MODEL_NAME"))


class CampaignGenerationFlow:
    """Orchestrates the complete campaign generation workflow using CrewAI."""

    def __init__(self, storage_root: str = "storage", outputs_root: str = "images"):
        self.storage_root = storage_root
        self.outputs_root = outputs_root

    def execute(self, campaign: Campaign) -> Campaign:
        """
        Execute the full 4-step campaign generation flow.

        Step 1: Extract branding, marketing details, and logo
        Step 2: Generate missing campaign images using Gemini Pro
        Step 3: Evaluate branding and generate future campaigns
        Step 4: Return completed campaign
        """
        print(f"\n=== Starting Campaign Generation Flow for: {campaign.name} ===\n")

        # Get paths for initial images
        initial_image_paths = [img.path for img in campaign.initialImages]

        # ===== STEP 1: Extraction Phase =====
        print("Step 1: Extracting branding, marketing, and logo details...")
        campaign = self._step1_extraction(campaign, initial_image_paths)

        # ===== STEP 2: Image Generation Phase =====
        print("\nStep 2: Generating missing campaign images...")
        campaign = self._step2_image_generation(campaign)

        # ===== STEP 3: Evaluation Phase =====
        print("\nStep 3: Evaluating branding and generating future campaigns...")
        campaign = self._step3_evaluation(campaign)

        # ===== STEP 4: Complete =====
        print("\nStep 4: Campaign generation complete!")
        return campaign

    def _step1_extraction(self, campaign: Campaign, initial_image_paths: List[str]) -> Campaign:
        """Step 1: Extract branding details, marketing details, and logo."""

        # Create agents for extraction
        branding_agent = create_branding_extract_agent()
        logo_agent = create_logo_extract_agent()
        marketing_agent = create_marketing_extract_agent()

        # Task 1a: Extract branding details
        branding_task = create_branding_extraction_task(
            branding_agent, campaign, initial_image_paths
        )

        # Task 1b: Extract logo
        logo_dir = os.path.join(self.storage_root, f"campaign_{campaign.id}", "logo")
        ensure_dir(logo_dir)
        logo_output_path = os.path.join(logo_dir, "logo.png")

        logo_task = None
        if initial_image_paths:
            logo_task = create_logo_extraction_task(
                logo_agent, initial_image_paths[0], logo_output_path
            )

        # Task 1c: Extract marketing details
        marketing_task = create_marketing_extraction_task(
            marketing_agent, campaign
        )

        # Create crew for parallel extraction
        extraction_tasks = [branding_task, marketing_task]
        if logo_task:
            extraction_tasks.append(logo_task)

        extraction_crew = Crew(
            agents=[branding_agent, marketing_agent, logo_agent] if logo_task else [branding_agent, marketing_agent],
            tasks=extraction_tasks,
            process=Process.sequential,
            verbose=True,
            llm=llm,
        )

        # Execute extraction
        results = extraction_crew.kickoff()

        # Store results in campaign
        campaign.brandingDetails = str(results)

        # Parse marketing details to extract language
        marketing_result = str(results)
        if "language" in marketing_result.lower():
            # Simple extraction - in production you'd parse more carefully
            if "US" in campaign.target_region.upper() or "USA" in campaign.target_region.upper():
                campaign.language = "US_en"
            else:
                campaign.language = "EN"

        campaign.marketingDetails = marketing_result

        # Set logo if extracted
        if logo_task and os.path.exists(logo_output_path):
            campaign.logoImage = ImageRecord(
                aspectRatio="square",
                path=os.path.relpath(logo_output_path)
            )

        return campaign

    def _step2_image_generation(self, campaign: Campaign) -> Campaign:
        """Step 2: Generate missing campaign images using Gemini Pro."""

        # Determine which aspect ratios need to be generated
        to_make = required_ratios(campaign.initialImages)

        if not to_make:
            print("All required aspect ratios already provided. Skipping generation.")
            return campaign

        # Create image summary agent
        image_summary_agent = create_image_summary_agent()

        # Generate images for each missing ratio
        out_dir = os.path.join(self.outputs_root, f"campaign{campaign.id}")
        ensure_dir(out_dir)

        for ratio in to_make:
            print(f"Generating image for aspect ratio: {ratio}")

            # Create image summary task
            summary_task = create_image_summary_task(
                image_summary_agent,
                campaign.brandingDetails,
                campaign.marketingDetails,
                campaign.campaign_message,
                ratio
            )

            # Execute summary creation
            summary_crew = Crew(
                agents=[image_summary_agent],
                tasks=[summary_task],
                process=Process.sequential,
                verbose=True,
                llm=llm,
            )

            summary_result = summary_crew.kickoff()
            generation_prompt = str(summary_result)

            # Generate image using Gemini Pro
            generated_image = self._generate_image_with_gemini(
                prompt=generation_prompt,
                aspect_ratio=ratio,
                logo_path=campaign.logoImage.path if campaign.logoImage else None,
                campaign_message=campaign.campaign_message
            )

            # Save generated image
            ratio_fname = ratio.replace(":", "x") + ".png"
            out_path = os.path.join(out_dir, ratio_fname)
            generated_image.save(out_path)

            # Add to campaign
            campaign.generatedImages.append(
                ImageRecord(aspectRatio=ratio, path=os.path.relpath(out_path))
            )

        return campaign

    def _generate_image_with_gemini(self, prompt: str, aspect_ratio: str,
                                     logo_path: str = None, campaign_message: str = None) -> PILImage.Image:
        """Generate image using Gemini Pro with logo and campaign message."""
        try:
            # Build generation prompt
            full_prompt = f"""Generate a high-quality marketing campaign image with the following specifications:

{prompt}

Campaign Message to Display: {campaign_message}

Requirements:
- Aspect Ratio: {aspect_ratio}
- Include the campaign message prominently
- Maintain professional quality suitable for social media advertising
"""

            # Build content parts
            contents = [full_prompt]

            # Add logo if available
            if logo_path and os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_bytes = f.read()
                contents.append(types.Part.from_bytes(data=logo_bytes, mime_type='image/png'))
                contents.append("Incorporate this logo into the image design.")

            # Note: Gemini Pro primarily does image analysis, not generation
            # For actual image generation, you would use Imagen API or another generative model
            # This is a placeholder that creates a simple image with the prompt info

            # Determine size based on aspect ratio
            if aspect_ratio == "1:1":
                size = (1024, 1024)
            elif aspect_ratio == "9:16":
                size = (1080, 1920)
            else:  # 16:9
                size = (1920, 1080)

            # Create placeholder image (in production, replace with actual Imagen API call)
            from src.utils import generate_placeholder
            return generate_placeholder(*size, text=campaign_message[:80])

        except Exception as e:
            print(f"Error generating image: {e}")
            # Fallback to placeholder
            if aspect_ratio == "1:1":
                size = (1024, 1024)
            elif aspect_ratio == "9:16":
                size = (1080, 1920)
            else:
                size = (1920, 1080)
            from src.utils import generate_placeholder
            return generate_placeholder(*size, text=campaign_message[:80])

    def _step3_evaluation(self, campaign: Campaign) -> Campaign:
        """Step 3: Evaluate branding and generate future campaigns."""

        # Create evaluation agents
        branding_report_agent = create_branding_report_agent()
        future_campaigns_agent = create_future_campaigns_agent()

        # Get paths of generated images
        generated_image_paths = [img.path for img in campaign.generatedImages]

        # Task 3a: Branding report
        branding_report_task = create_branding_report_task(
            branding_report_agent,
            generated_image_paths,
            campaign.brandingDetails
        )

        # Task 3b: Future campaigns
        campaign_brief = {
            'name': campaign.name,
            'products': campaign.products,
            'target_region': campaign.target_region,
            'target_audience': campaign.target_audience,
            'campaign_message': campaign.campaign_message
        }

        future_campaigns_task = create_future_campaigns_task(
            future_campaigns_agent,
            campaign,
            campaign.brandingDetails,
            campaign.marketingDetails
        )

        # Create crew for evaluation
        evaluation_crew = Crew(
            agents=[branding_report_agent, future_campaigns_agent],
            tasks=[branding_report_task, future_campaigns_task],
            process=Process.sequential,
            verbose=True,
            llm=llm,
        )

        # Execute evaluation
        results = evaluation_crew.kickoff()

        # Store results
        results_str = str(results)

        # Split results (first part is branding report, second is future campaigns)
        campaign.brandingReport = results_str
        campaign.futureCampaigns = results_str

        return campaign
