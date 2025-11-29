from google.adk.agents import LlmAgent
from tools.market import get_caiso_market_data
from prompts.market import get_market_instructions


MARKET_INSTRUCTIONS = get_market_instructions()

market_agent = LlmAgent(
    name="CAISO_Market", 
    description="Handles specific CAISO market data requests like Load, Fuel Mix, and LMPs.", 
    tools=[get_caiso_market_data],
    instruction=MARKET_INSTRUCTIONS
)