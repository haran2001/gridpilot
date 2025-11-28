from google.adk.agents import LlmAgent
from agents.weather import weather_impact_agent
from agents.market import market_agent

orchestrator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    instruction="""
    When analyzing weather impact on a node's price:
    
    1. First call get_weather_locations_for_node to understand WHICH locations matter
    2. Then fetch weather for those specific locations
    3. Consider both:
       - Load impact: High temps → more AC → higher demand → higher prices
       - Supply impact: Clouds/low wind → less renewables → higher net load → higher prices
    
    The relative importance varies by zone:
    - SP15: Balance of load (LA heat) and solar (desert)
    - ZP26: Solar-dominated, clouds matter more than temperature
    - NP15: Load-dominated, SF/Sacramento temps matter most
    """,
    sub_agents=[weather_impact_agent, market_agent]
)