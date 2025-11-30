from google.adk.agents import LlmAgent
from agents.weather import weather_impact_agent
from agents.market import market_agent
from agents.grid import grid_agent
from prompts.orchestrator import get_orchestrator_instructions
from dotenv import load_dotenv
import os

load_dotenv()

MODEL = os.getenv("MODEL")
ORCHESTRATOR_INSTRUCTIONS = get_orchestrator_instructions()

orchestrator = LlmAgent(
    name="Coordinator",
    model="gemini-3-pro-preview",
    instruction=ORCHESTRATOR_INSTRUCTIONS,
    sub_agents=[weather_impact_agent, market_agent, grid_agent]
)