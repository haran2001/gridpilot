import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv



import gridstatus

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

geolocator = Nominatim(user_agent="weather-app")

class SearchInput(BaseModel):
    location:str = Field(description="The city and state, e.g., San Francisco")
    date:str = Field(description="the forecasting date for when to get the weather format (yyyy-mm-dd)")

@tool("get_weather_forecast", args_schema=SearchInput, return_direct=True)
def get_weather_forecast(location: str, date: str):
    """Retrieves the weather using Open-Meteo API for a given location (city) and a date (yyyy-mm-dd). Returns a list dictionary with the time and temperature for each hour."""
    location = geolocator.geocode(location)
    if location:
        try:
            response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={location.latitude}&longitude={location.longitude}&hourly=temperature_2m&start_date={date}&end_date={date}")
            data = response.json()
            return {time: temp for time, temp in zip(data["hourly"]["time"], data["hourly"]["temperature_2m"])}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Location not found"}

llm = ChatGoogleGenerativeAI(
    model= "gemini-2.0-flash",
    temperature=1.0,
    max_retries=2,
    google_api_key=api_key,
)

model = llm.bind_tools([get_weather_forecast])

messages = [HumanMessage(content=f"What is the weather in Berlin on {datetime.today()}?")]
res = model.invoke(messages)
messages.append(res)

if res.tool_calls:
    for tool_call in res.tool_calls:
        if tool_call["name"] == "get_weather_forecast":
            tool_output = get_weather_forecast.invoke(tool_call["args"])
            print("Tool Output:", tool_output)
            messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(tool_output)))
    
    final_res = model.invoke(messages)
    print("Final Response:", final_res.content)
else:
    print(res.content)