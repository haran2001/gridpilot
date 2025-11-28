import gridstatus
from typing import List, Optional
import requests
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="gridpilot")

# Common CAISO pricing nodes for reference
CAISO_HUBS = {
    "NP15": "TH_NP15_GEN-APND",  # North (SF, Sacramento)
    "SP15": "TH_SP15_GEN-APND",  # South (LA, San Diego)
    "ZP26": "TH_ZP26_GEN-APND",  # Central (Fresno)
}

# CAISO node coordinates (you'd load this from CAISO's master node file)
NODE_COORDINATES = {
    "TH_NP15_GEN-APND": {"lat": 38.5, "lon": -121.5, "zone": "NP15", "type": "HUB"},
    "TH_SP15_GEN-APND": {"lat": 34.0, "lon": -118.2, "zone": "SP15", "type": "HUB"},
    "TH_ZP26_GEN-APND": {"lat": 36.7, "lon": -119.8, "zone": "ZP26", "type": "HUB"},
}

# Major weather-sensitive locations in CAISO
CAISO_WEATHER_POINTS = {
    # Load centers (temperature → AC demand)
    "load": [
        {"name": "Los Angeles, CA", "lat": 34.05, "lon": -118.24, "zone": "SP15", "population": 4_000_000},
        {"name": "San Diego, CA", "lat": 32.72, "lon": -117.16, "zone": "SP15", "population": 1_400_000},
        {"name": "San Francisco, CA", "lat": 37.77, "lon": -122.42, "zone": "NP15", "population": 870_000},
        {"name": "Sacramento, CA", "lat": 38.58, "lon": -121.49, "zone": "NP15", "population": 525_000},
        {"name": "San Jose, CA", "lat": 37.34, "lon": -121.89, "zone": "NP15", "population": 1_000_000},
        {"name": "Fresno, CA", "lat": 36.74, "lon": -119.79, "zone": "ZP26", "population": 540_000},
        {"name": "Riverside, CA", "lat": 33.95, "lon": -117.40, "zone": "SP15", "population": 330_000},
    ],
    # Solar generation centers (cloud cover, irradiance)
    "solar": [
        {"name": "Mojave Desert, CA", "lat": 35.05, "lon": -117.50, "zone": "SP15", "capacity_mw": 3000},
        {"name": "Imperial Valley, CA", "lat": 32.85, "lon": -115.57, "zone": "SP15", "capacity_mw": 1500},
        {"name": "Westlands, CA", "lat": 36.20, "lon": -120.10, "zone": "ZP26", "capacity_mw": 2500},
    ],
    # Wind generation centers
    "wind": [
        {"name": "Tehachapi, CA", "lat": 35.13, "lon": -118.45, "zone": "SP15", "capacity_mw": 1000},
        {"name": "Altamont Pass, CA", "lat": 37.73, "lon": -121.65, "zone": "NP15", "capacity_mw": 500},
    ]
}

def get_weather_locations_for_node(node_id: str) -> dict:
    """
    Determines which weather locations are relevant for predicting 
    price at a given CAISO node.
    
    Returns locations for both load (temperature-driven demand) and 
    renewables (generation that sets marginal price).
    """
    
    # Resolve node
    if node_id.upper() in ["NP15", "SP15", "ZP26"]:
        node_id = f"TH_{node_id.upper()}_GEN-APND"
    
    node = NODE_COORDINATES.get(node_id)
    if not node:
        return {"error": f"Unknown node: {node_id}. Try NP15, SP15, or ZP26."}
    
    zone = node["zone"]
    node_location = (node["lat"], node["lon"])
    
    # Get load centers in this zone, weighted by population
    zone_loads = [loc for loc in CAISO_WEATHER_POINTS["load"] if loc["zone"] == zone]
    zone_loads_sorted = sorted(zone_loads, key=lambda x: x["population"], reverse=True)
    
    # Get renewable locations - these matter system-wide for price
    # but especially for nodes in high-solar zones
    zone_solar = [loc for loc in CAISO_WEATHER_POINTS["solar"] if loc["zone"] == zone]
    all_solar = CAISO_WEATHER_POINTS["solar"]  # Solar anywhere affects system price
    
    zone_wind = [loc for loc in CAISO_WEATHER_POINTS["wind"] if loc["zone"] == zone]
    
    # Determine weighting based on zone characteristics
    if zone == "SP15":
        load_weight = 0.5
        solar_weight = 0.4
        wind_weight = 0.1
        note = "SP15 is load-heavy (LA) but solar significantly impacts mid-day prices"
    elif zone == "ZP26":
        load_weight = 0.3
        solar_weight = 0.6
        wind_weight = 0.1
        note = "ZP26 (Central) is dominated by utility-scale solar"
    else:  # NP15
        load_weight = 0.7
        solar_weight = 0.2
        wind_weight = 0.1
        note = "NP15 is more load-driven; less local solar impact"
    
    return {
        "node_id": node_id,
        "zone": zone,
        "analysis_note": note,
        "weather_locations": {
            "load_centers": {
                "locations": [loc["name"] for loc in zone_loads_sorted[:3]],
                "weight": load_weight,
                "metric": "temperature (drives AC demand)"
            },
            "solar_generation": {
                "locations": [loc["name"] for loc in zone_solar] or [loc["name"] for loc in all_solar[:2]],
                "weight": solar_weight,
                "metric": "cloud cover, irradiance (drives solar output)"
            },
            "wind_generation": {
                "locations": [loc["name"] for loc in zone_wind] or ["Tehachapi, CA"],
                "weight": wind_weight,
                "metric": "wind speed (drives wind output)"
            }
        },
        "recommended_query": f"For {node_id}, check temps in {zone_loads_sorted[0]['name'] if zone_loads_sorted else 'N/A'} "
                            f"and solar conditions in {zone_solar[0]['name'] if zone_solar else 'Mojave Desert, CA'}"
    }

def get_caiso_forecasts(
    date: str,
    locations: Optional[List[str]] = None
):
    """
    Fetches CAISO's own demand and renewable forecasts for a given date.
    
    Args:
        date: Forecast date in YYYY-MM-DD format
        locations: List of pricing nodes. Can be shorthand ("NP15", "SP15", "ZP26") 
                   or full node IDs ("TH_NP15_GEN-APND"). 
                   Defaults to NP15 and SP15 if not specified.
    
    Returns:
        Dict with load forecast and day-ahead LMPs for requested locations.
    """
    try:
        iso = gridstatus.CAISO()
        
        # Resolve location shorthand to full node IDs
        if locations is None:
            locations = ["NP15", "SP15"]
        
        resolved_locations = []
        for loc in locations:
            if loc.upper() in CAISO_HUBS:
                resolved_locations.append(CAISO_HUBS[loc.upper()])
            else:
                # Assume it's already a full node ID
                resolved_locations.append(loc)
        
        # CAISO publishes load forecasts (system-wide, not nodal)
        load_forecast = iso.get_load_forecast(date)
        
        # Day-ahead prices for specified nodes
        dam_prices = iso.get_lmp(
            date=date,
            market="DAY_AHEAD_HOURLY",
            locations=resolved_locations
        )
        
        return {
            "date": date,
            "locations_queried": resolved_locations,
            "load_forecast": load_forecast.to_dict(),
            "day_ahead_lmp": dam_prices.to_dict()
        }
    except Exception as e:
        return f"Error: {str(e)}"

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