"""
CrewAI Task Definitions for Campaign Generation Flow
"""
from crewai import Task
from typing import List
from models import Campaign


def create_branding_extraction_task(agent, campaign: Campaign, image_paths: List[str]) -> Task:
    """Task for extracting branding details from images and campaign brief."""
    return Task(
        description=f"""Analyze the provided images and campaign details to extract comprehensive branding guidelines.

Campaign Details:
- Products: {', '.join(campaign.products)}
- Target Audience: {campaign.target_audience}
- Campaign Message: {campaign.campaign_message}
- Images to analyze: {', '.join(image_paths)}

Extract detailed branding information including logo characteristics, color palette, typography, visual tone, and brand elements to include or avoid in generated images.""",
        expected_output="A structured branding guide with logo details, color palette, typography, visual tone, and specific guidelines for image generation.",
        agent=agent
    )


def create_logo_extraction_task(agent, image_path: str, output_path: str) -> Task:
    """Task for extracting logo from uploaded image."""
    return Task(
        description=f"""Extract the primary logo from the provided image and save it for later use in image generation.

Input Image: {image_path}
Output Path: {output_path}

Identify and isolate the logo, then save it as a separate image file that can be used in the image generation process.""",
        expected_output=f"Logo extracted and saved to {output_path} with confirmation of successful extraction.",
        agent=agent
    )


def create_marketing_extraction_task(agent, campaign: Campaign) -> Task:
    """Task for extracting marketing details based on region and audience."""
    return Task(
        description=f"""Analyze the target market and audience to extract marketing insights and trends.

Target Region: {campaign.target_region}
Target Audience: {campaign.target_audience}
Campaign Message: {campaign.campaign_message}

Research and provide:
1. Language and cultural considerations
2. Current trends relevant to the target audience
3. Refined marketing message with professional guardrails
4. Audience engagement strategies
5. Performance optimization recommendations""",
        expected_output="A comprehensive marketing analysis including language recommendations, cultural insights, trends, refined messaging, and engagement strategies.",
        agent=agent
    )


def create_image_summary_task(agent, branding_details: str, marketing_details: str,
                               campaign_message: str, aspect_ratio: str) -> Task:
    """Task for creating image generation prompt from branding and marketing details."""
    return Task(
        description=f"""Create a detailed image generation prompt optimized for {aspect_ratio} aspect ratio.

Campaign Message: {campaign_message}
Aspect Ratio: {aspect_ratio}

Use the following context:
Branding Details: {branding_details[:500]}...
Marketing Details: {marketing_details[:500]}...

Synthesize all information into a comprehensive prompt that will guide AI image generation while maintaining brand consistency and marketing effectiveness.""",
        expected_output=f"A detailed, structured image generation prompt optimized for {aspect_ratio} format that incorporates branding and marketing guidelines.",
        agent=agent
    )


def create_branding_report_task(agent, generated_image_paths: List[str],
                                 branding_details: str) -> Task:
    """Task for evaluating generated images against branding guidelines."""
    return Task(
        description=f"""Evaluate the generated campaign images against the established branding guidelines.

Generated Images: {', '.join(generated_image_paths)}

Branding Guidelines:
{branding_details[:500]}...

For each image, provide:
1. Branding alignment score (0-10)
2. Strengths and positive elements
3. Areas for improvement
4. Specific recommendations

Create a comprehensive branding evaluation report.""",
        expected_output="A detailed branding report with scores, analysis of what's working, areas for improvement, and actionable recommendations for each generated image.",
        agent=agent
    )


def create_future_campaigns_task(agent, campaign: Campaign, branding_details: str,
                                  marketing_details: str) -> Task:
    """Task for generating future campaign ideas."""
    return Task(
        description=f"""Generate 3 future campaign ideas for the next 3 months based on the current campaign.

Current Campaign:
- Name: {campaign.name}
- Products: {', '.join(campaign.products)}
- Target Region: {campaign.target_region}
- Target Audience: {campaign.target_audience}
- Campaign Message: {campaign.campaign_message}

Context:
Branding: {branding_details[:500]}...
Marketing: {marketing_details[:500]}...

For each month, create a complete campaign brief including:
1. Campaign name and theme
2. Products to feature
3. Target audience refinements
4. Campaign message
5. Strategic rationale
6. Expected outcomes

Focus on building a cohesive 3-month strategy.""",
        expected_output="3 detailed campaign briefs for the next 3 months, each with complete details, strategic rationale, and expected outcomes.",
        agent=agent
    )
