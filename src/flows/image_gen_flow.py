from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from google.genai import types
from PIL import Image as PILImage

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

@CrewBase
class ImageGenCrew:
    """Image Generation Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
