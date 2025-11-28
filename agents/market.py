from google.adk.agents import LlmAgent
from tools.market import get_caiso_market_data

market_agent = LlmAgent(
    name="CAISO_Market", 
    description="Handles specific CAISO market data requests like Load, Fuel Mix, and LMPs.", 
    tools=[get_caiso_market_data]
)