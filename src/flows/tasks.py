"""
CrewAI Task Definitions for Campaign Generation Flow
"""
from crewai import Task
from typing import List
from src.models import Campaign


def create_branding_extraction_task(agent, campaign: Campaign) -> Task:
    """Task for extracting branding details from logo and campaign brief."""
    return Task(
        description=f"""Analyze the provided logo and campaign details to extract comprehensive branding guidelines.

Campaign Details:
- Products: {', '.join(campaign.products)}
- Target Audience: {campaign.target_audience}
- Campaign Message: {campaign.campaign_message}
- Logo path: {campaign.logo_path}

Extract detailed branding information including logo characteristics, color palette, typography, visual tone, and brand elements to include or avoid in generated images.""",
        expected_output="A structured branding guide with logo details, color palette, typography, visual tone, and specific guidelines for image generation.",
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


def create_branding_report_task(agent, generated_image_path: str, logo_path: str,
                                 branding_details: str) -> Task:
    """Task for evaluating a single generated image against branding guidelines."""
    return Task(
        description=f"""Evaluate the generated campaign image against the established branding guidelines and verify logo inclusion.

Generated Image: {generated_image_path}
Logo Reference: {logo_path}

Branding Guidelines:
{branding_details[:500]}...

Provide:
1. Branding alignment score (0-10)
2. Logo detection - Is the input logo actually included in the generated image? (Yes/No and details)
3. Strengths and positive elements
4. Areas for improvement
5. Specific recommendations

IMPORTANT: Verify whether the logo from {logo_path} appears in the generated image.""",
        expected_output="A detailed branding report with score, logo detection confirmation, analysis of what's working, areas for improvement, and actionable recommendations.",
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
