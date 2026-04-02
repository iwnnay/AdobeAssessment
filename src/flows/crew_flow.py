"""
CrewAI Flow for Campaign Image Generation
Orchestrates the 4-step process as defined in the requirements
"""
import os
import random
from typing import List
from crewai import Crew, Process, LLM
from google.genai import types
from PIL import Image as PILImage

from src.database import Database
from src.models import Campaign, ImageRecord, MarketingExtraction, ImageSummary
from src.flows.agents import (
    create_branding_extract_agent,
    create_marketing_extract_agent,
    create_image_summary_agent,
    create_branding_report_agent,
    create_future_campaigns_agent
)
from src.flows.tasks import (
    create_branding_extraction_task,
    create_marketing_extraction_task,
    create_image_summary_task,
    create_branding_report_task,
    create_future_campaigns_task
)
from src.utils import ensure_dir, required_ratios
from dotenv import load_dotenv

load_dotenv()
# Configure Gemini client with new API
llm = LLM(model=f"gemini/{os.getenv("GEMINI_CHAT_MODEL_NAME")}")


class CampaignGenerationFlow:
    """Orchestrates the complete campaign generation workflow using CrewAI."""

    def __init__(self, storage_root: str = "storage"):
        self.storage_root = storage_root

    def execute(self, campaign: Campaign) -> Campaign:
        """
        Execute the full 4-step campaign generation flow.

        Step 1: Extract branding, marketing details
        Step 2: Generate missing campaign images using Gemini Pro
        Step 3: Evaluate branding and generate future campaigns
        Step 4: Return completed campaign
        """
        print(f"\n=== Starting Campaign Generation Flow for: {campaign.name} ===\n")

        # ===== STEP 1: Extraction Phase =====
        print("Step 1: Extracting branding, and marketing details...")
        campaign = self._step1_extraction(campaign)

        # ===== STEP 2: Image Generation Phase =====
        print("\nStep 2: Generating missing campaign images...")
        campaign = self._step2_image_generation(campaign)

        # ===== STEP 3: Evaluation Phase =====
        print("\nStep 3: Evaluating branding and generating future campaigns...")
        campaign = self._step3_evaluation(campaign)

        # ===== STEP 4: Complete =====
        print("\nStep 4: Campaign generation complete!")
        return campaign

    def _step1_extraction(self, campaign: Campaign) -> Campaign:
        """Step 1: Extract branding details, marketing details, and logo."""

        # Create agents for extraction
        branding_agent = create_branding_extract_agent()
        marketing_agent = create_marketing_extract_agent()

        # Task 1a: Extract branding details
        branding_task = create_branding_extraction_task(
            branding_agent, campaign,
        )

        # Task 1c: Extract marketing details
        marketing_task = create_marketing_extraction_task(
            marketing_agent, campaign
        )

        # Create crew for parallel extraction
        extraction_tasks = [branding_task, marketing_task]

        extraction_crew = Crew(
            agents=[branding_agent, marketing_agent],
            tasks=extraction_tasks,
            process=Process.sequential,
            verbose=True,
            llm=llm,
        )

        # Execute extraction
        results = extraction_crew.kickoff()

        # Extract branding details (first task result)
        campaign.brandingDetails = str(results.tasks_output[0])

        # Extract marketing details (second task result - Pydantic object)
        marketing_result = results.tasks_output[1]

        # Check if we got a MarketingExtraction object or just a string
        if isinstance(marketing_result.pydantic, MarketingExtraction):
            # Use the structured Pydantic output
            campaign.language = marketing_result.pydantic.language
            campaign.marketingDetails = marketing_result.pydantic.marketing_research
        else:
            # Fallback to string parsing if Pydantic didn't work
            marketing_str = str(marketing_result)
            campaign.marketingDetails = marketing_str
            # Simple fallback language detection
            if "US" in campaign.target_region.upper() or "USA" in campaign.target_region.upper():
                campaign.language = "US_en"
            else:
                campaign.language = "EN"

        return campaign

    def _step2_image_generation(self, campaign: Campaign) -> Campaign:
        """Step 2: Generate missing campaign images using Gemini Pro."""

        # Determine which aspect ratios need to be generated
        to_make = required_ratios()

        # Create image summary agent
        image_summary_agent = create_image_summary_agent()

        # Generate images for each missing ratio
        out_dir = os.path.join(self.storage_root, f"campaign{campaign.id}")
        ensure_dir(out_dir)

        for ratio in to_make:
            print(f"Generating image for aspect ratio: {ratio}")

            # Create image summary task with language for translation
            summary_task = create_image_summary_task(
                image_summary_agent,
                campaign.brandingDetails,
                campaign.marketingDetails,
                campaign.campaign_message,
                ratio,
                campaign.language
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

            # Extract structured output from the task result
            if isinstance(summary_result.pydantic, ImageSummary):
                generation_prompt = summary_result.pydantic.generation_prompt
                translated_message = summary_result.pydantic.translated_message
            else:
                # Fallback if Pydantic didn't work
                generation_prompt = str(summary_result)
                translated_message = campaign.campaign_message

            print(f"Translated message ({campaign.language}): {translated_message}")

            # Generate image using Gemini Pro with translated message
            generated_image = self._generate_image_with_gemini(
                prompt=generation_prompt,
                aspect_ratio=ratio,
                logo_path=campaign.logo_path,
                campaign_message=translated_message
            )

            # Save generated image
            ratio_fname = ratio.replace(":", "x") + ".png"
            out_path = os.path.join(out_dir, ratio_fname)
            generated_image.save(out_path)

            # Add to campaign
            campaign.generated_images.append(
                ImageRecord(aspectRatio=ratio, path=os.path.relpath(out_path))
            )

        return campaign

    def _generate_image_with_gemini(self, prompt: str, aspect_ratio: str,
                                     logo_path: str = None, campaign_message: str = None) -> PILImage.Image:
        """Generate image using Gemini 2.0 Flash with multimodal generation."""
        try:
            from google import genai
            import io

            # Initialize client
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            # Build generation prompt
            full_prompt = f"""Generate a professional marketing campaign image with these specifications:

{prompt}

Campaign Message to display: "{campaign_message}"

Requirements:
- Aspect Ratio: {aspect_ratio}
- Include the campaign message text prominently and clearly in the design
- High quality, professional marketing aesthetic suitable for social media
- Modern, eye-catching, visually appealing design
"""

            if logo_path and os.path.exists(logo_path):
                logo_image = PILImage.open(logo_path)
                full_prompt += "\n\n naturally incorporate the logo image into the design"
            else:
                raise Exception("No logo image provided")

            contents = [full_prompt, logo_image]

            print(f"Generating image with Gemini 2.0 Flash for {aspect_ratio} with {full_prompt}...\n\n{os.getenv('GEMINI_MODEL_NAME')}")

            # Generate image using Gemini 2.0 Flash multimodal generation
            response = client.models.generate_content(
                model=os.getenv("GEMINI_IMAGE_MODEL_NAME"),
                contents=contents,
            )

            for part in response.parts:
                if part.text:
                    print(part.text)
                elif part.inline_data:
                    image = part.as_image()
                    return image

            raise Exception(f"No image generated {response}")

        except Exception as e:
            print(f"Falling back to placeholder image... {e}")
            # Fallback to placeholder
            if aspect_ratio == "1:1":
                size = (1024, 1024)
            elif aspect_ratio == "9:16":
                size = (1080, 1920)
            else:
                size = (1920, 1080)
            from src.utils import generate_placeholder
            return generate_placeholder(*size, text=f"Failed to generate: {campaign_message[:60]}")

    def _step3_evaluation(self, campaign: Campaign) -> Campaign:
        """Step 3: Evaluate each image's branding and generate future campaigns."""

        # Create evaluation agents
        branding_report_agent = create_branding_report_agent()
        future_campaigns_agent = create_future_campaigns_agent()

        # Task 3a: Evaluate each generated image individually
        for i, image_record in enumerate(campaign.generated_images):
            print(f"Evaluating image {i+1}/{len(campaign.generated_images)}: {image_record.path}")

            branding_report_task = create_branding_report_task(
                branding_report_agent,
                image_record.path,
                campaign.logo_path,
                campaign.brandingDetails
            )

            # Create crew for this image's evaluation
            image_evaluation_crew = Crew(
                agents=[branding_report_agent],
                tasks=[branding_report_task],
                process=Process.sequential,
                verbose=True
            )

            # Execute evaluation for this image
            branding_result = image_evaluation_crew.kickoff()

            # Store branding report in the image record
            image_record.brandingReport = str(branding_result)

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

        # Create crew for future campaigns
        future_campaigns_crew = Crew(
            agents=[future_campaigns_agent],
            tasks=[future_campaigns_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute future campaigns generation
        future_result = future_campaigns_crew.kickoff()

        # Store future campaigns result
        campaign.futureCampaigns = str(future_result)

        return campaign
