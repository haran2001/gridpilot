
from google.adk.agents import LlmAgent
from prompts.weather import get_weather_instructions
from tools.weather import get_weather_locations_for_node, get_weather_forecast, get_caiso_forecasts
from dotenv import load_dotenv
import os

load_dotenv()

MODEL = os.getenv("MODEL")
WEATHER_AGENT_INSTRUCTIONS = get_weather_instructions()

weather_impact_agent = LlmAgent(
    name="Weather_Impact_Analyst",
    instruction=WEATHER_AGENT_INSTRUCTIONS,
    description="Maps CAISO nodes to relevant weather locations and analyzes price impacts.",
    tools=[get_weather_locations_for_node, get_weather_forecast, get_caiso_forecasts]
)