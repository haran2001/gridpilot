from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.apps.app import App
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.genai import types
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from geopy.geocoders import Nominatim
import requests
from datetime import datetime
import pandas as pd
import gridstatus

# Load environment variables
load_dotenv()

geolocator = Nominatim(user_agent="gridpilot")

# --- Tool Definitions ---

def get_weather_forecast(location: str, date: str):
    """
    Retrieves the weather using Open-Meteo API for a given location and date.
    Returns a simplified summary of the day's temperature curve.
    """
    try:
        loc = geolocator.geocode(location)
        if not loc:
            return {"error": f"Location '{location}' not found"}
            
        # Fetching hourly temperature
        url = f"https://api.open-meteo.com/v1/forecast?latitude={loc.latitude}&longitude={loc.longitude}&hourly=temperature_2m&start_date={date}&end_date={date}"
        response = requests.get(url)
        data = response.json()
        
        if "error" in data:
            return {"error": data["reason"]}

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        
        # summarizing to save token context
        summary = {
            "location": location,
            "date": date,
            "max_temp": max(temps) if temps else None,
            "min_temp": min(temps) if temps else None,
            "noon_temp": temps[12] if len(temps) > 12 else None,
            "evening_peak_temp_1800": temps[18] if len(temps) > 18 else None
        }
        return str(summary)
    except Exception as e:
        return f"Failed to fetch weather: {str(e)}"

def get_caiso_market_data():
    """
    Fetches real-time CAISO market data including Load, Net Load (Load - Solar - Wind),
    and Locational Marginal Prices (LMPs) for key trading hubs (NP15, SP15).
    """
    try:
        iso = gridstatus.CAISO()
        
        # 1. Get Load and Renewables (Fuel Mix)
        # gridstatus returns pandas DataFrames. We need the latest interval.
        fuel_mix_df = iso.get_fuel_mix("latest")
        load_df = iso.get_load("latest")
        
        # Extract latest values
        latest_mix = fuel_mix_df.iloc[-1]
        latest_load_row = load_df.iloc[-1]
        
        current_load = latest_load_row["Load"]
        current_solar = latest_mix.get("Solar", 0)
        current_wind = latest_mix.get("Wind", 0)
        
        # Calculate Net Load - The most critical metric for CAISO traders
        net_load = current_load - current_solar - current_wind
        
        # 2. Get Pricing (LMP) for Trading Hubs
        # We focus on NP15 (North) and SP15 (South) to see congestion spreads
        # Using Real-Time Market (RTM) 5-min prices
        lmp_df = iso.get_lmp("latest", market="REAL_TIME_5_MIN", locations=["TH_NP15_GEN-APND", "TH_SP15_GEN-APND"])
        
        # Pivot or filter to get a clean view
        latest_lmps = lmp_df.tail(2)[["Location", "LMP", "Congestion", "Energy", "Loss"]]
        
        summary = (
            f"--- CAISO Real-Time Snapshot ---\n"
            f"Time: {latest_load_row['Time']}\n"
            f"System Load: {current_load} MW\n"
            f"Renewables: Solar {current_solar} MW | Wind {current_wind} MW\n"
            f"Net Load: {net_load} MW (Load - Renewables)\n\n"
            f"--- Key Hub Pricing (5-Min RTM) ---\n"
            f"{latest_lmps.to_string(index=False)}\n"
        )
        
        return summary

    except Exception as e:
        return f"Error fetching CAISO data: {str(e)}"

# --- Agent Configuration ---

weather_agent = LlmAgent(
    name="Weather", 
    description="Handles weather requests for specific locations.", 
    tools=[get_weather_forecast]
)

market_agent = LlmAgent(
    name="CAISO_Market", 
    description="Handles specific CAISO market data requests like Load, Fuel Mix, and LMPs.", 
    tools=[get_caiso_market_data]
)

# I've updated the instructions to reflect how an analyst thinks about correlation.
# We care about how temperature (AC demand) drives Load, and how Solar drives Net Load.
coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    instruction="""
    You are a Senior Power Market Analyst for the CAISO desk. 
    Your goal is to synthesize weather and market data to provide actionable insights.
    
    1. Weather drives Load: High temps in LA (SP15) or SF (NP15) increase demand.
    2. Renewables drive Price: High Solar pushes Net Load down, often crashing mid-day prices.
    3. Geography matters: If user asks about 'CAISO weather', check both 'San Francisco' (North/NP15) and 'Los Angeles' (South/SP15).
    
    When answering:
    - First, get the market conditions (Load, Net Load, Prices).
    - Second, get the weather context if relevant.
    - Finally, explain the relationship. (e.g., "Prices are soft despite high temps because solar output is crushing the Net Load.")
    """,
    description="Main coordinator for power analysis.",
    sub_agents=[weather_agent, market_agent]
)

# --- Main Execution ---

async def main():
    # A realistic analyst query: checking the "health" of the market
    user_query = f"Analyze the current status of the CAISO market. How is the weather in Los Angeles impacting the load?"
    print(f"User: {user_query}")
    
    # Setup services
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    credential_service = InMemoryCredentialService()
    
    # Create App and Runner
    app = App(name="GridPilot", root_agent=coordinator)
    runner = Runner(
        app=app,
        session_service=session_service,
        artifact_service=artifact_service,
        credential_service=credential_service
    )
    
    # Create session
    session = await session_service.create_session(app_name="GridPilot", user_id="tim_ennis")
    
    # Run agent
    content = types.Content(role='user', parts=[types.Part(text=user_query)])
    async for event in runner.run_async(user_id="tim_ennis", session_id=session.id, new_message=content):
        if event.content and event.content.parts:
             print(f"[{event.author}]: {event.content.parts[0].text}")

if __name__ == "__main__":
    asyncio.run(main())