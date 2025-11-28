"""
Grid tools for CAISO data retrieval and analysis.
Uses the gridstatus library for API access.
"""

from datetime import datetime
from typing import Any
import pandas as pd
import gridstatus

# Initialize CAISO client
caiso = gridstatus.CAISO()


def get_caiso_demand(
    date: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Get CAISO real-time demand data in 5-minute intervals.
    
    Args:
        date: Date in YYYY-MM-DD format or "today"/"latest". Defaults to "latest".
        end: End date for range queries. Optional.
    
    Returns:
        Dictionary with demand data including current load and timestamps.
    """
    if date is None:
        date = "latest"
    
    try:
        df = caiso.get_load(date=date, end=end)
        
        if df.empty:
            return {"error": "No data available", "date": date}
        
        latest = df.iloc[-1]
        
        return {
            "date": date,
            "current_demand_mw": float(latest["Load"]),
            "interval_start": latest["Interval Start"].isoformat(),
            "interval_end": latest["Interval End"].isoformat(),
            "data_points": len(df),
            "min_demand_mw": float(df["Load"].min()),
            "max_demand_mw": float(df["Load"].max()),
            "avg_demand_mw": float(df["Load"].mean()),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def get_caiso_load_forecast(
    date: str | None = None,
    end: str | None = None,
    forecast_type: str = "day_ahead",
) -> dict[str, Any]:
    """
    Get CAISO load forecast data.
    
    Args:
        date: Date in YYYY-MM-DD format or "today". Defaults to today.
        end: End date for range queries. Optional.
        forecast_type: One of "day_ahead", "hour_ahead_15min", "hour_ahead_5min", 
                       "two_day_ahead", "seven_day_ahead"
    
    Returns:
        Dictionary with forecast data.
    """
    if date is None:
        date = "today"
    
    try:
        if forecast_type == "day_ahead":
            df = caiso.get_load_forecast_day_ahead(date=date, end=end)
        elif forecast_type == "hour_ahead_15min":
            df = caiso.get_load_forecast_15_min(date=date, end=end)
        elif forecast_type == "hour_ahead_5min":
            df = caiso.get_load_forecast_5_min(date=date, end=end)
        elif forecast_type == "two_day_ahead":
            df = caiso.get_load_forecast_two_day_ahead(date=date, end=end)
        elif forecast_type == "seven_day_ahead":
            df = caiso.get_load_forecast_seven_day_ahead(date=date, end=end)
        else:
            return {"error": f"Invalid forecast_type: {forecast_type}"}
        
        if df.empty:
            return {"error": "No forecast data available", "date": date}
        
        # Filter to CA ISO-TAC (total CAISO)
        df_total = df[df["TAC Area Name"] == "CA ISO-TAC"]
        
        if df_total.empty:
            df_total = df
        
        return {
            "date": date,
            "forecast_type": forecast_type,
            "forecasts": df_total[["Interval Start", "Interval End", "Load Forecast"]].to_dict(orient="records"),
            "peak_forecast_mw": float(df_total["Load Forecast"].max()),
            "min_forecast_mw": float(df_total["Load Forecast"].min()),
            "avg_forecast_mw": float(df_total["Load Forecast"].mean()),
            "data_points": len(df_total),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date, "forecast_type": forecast_type}


def get_caiso_supply_mix(
    date: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Get CAISO fuel mix (generation by source) in 5-minute intervals.
    
    Args:
        date: Date in YYYY-MM-DD format or "today"/"latest". Defaults to "latest".
        end: End date for range queries. Optional.
    
    Returns:
        Dictionary with generation by fuel type in MW and percentages.
    """
    if date is None:
        date = "latest"
    
    try:
        df = caiso.get_fuel_mix(date=date, end=end)
        
        if df.empty:
            return {"error": "No data available", "date": date}
        
        latest = df.iloc[-1]
        
        # Get all fuel columns (exclude Time, Interval Start, Interval End)
        fuel_columns = [col for col in df.columns 
                       if col not in ["Time", "Interval Start", "Interval End"]]
        
        generation_mw = {}
        total_mw = 0
        
        for col in fuel_columns:
            val = float(latest[col]) if pd.notna(latest[col]) else 0
            generation_mw[col] = val
            total_mw += val
        
        # Calculate percentages
        percentages = {}
        for col, val in generation_mw.items():
            percentages[col] = round((val / total_mw) * 100, 1) if total_mw > 0 else 0
        
        # Calculate renewables total
        renewable_sources = ["Solar", "Wind", "Small Hydro", "Biogas", "Biomass", "Geothermal"]
        renewables_mw = sum(generation_mw.get(src, 0) for src in renewable_sources)
        renewables_pct = round((renewables_mw / total_mw) * 100, 1) if total_mw > 0 else 0
        
        return {
            "date": date,
            "interval_start": latest["Interval Start"].isoformat(),
            "interval_end": latest["Interval End"].isoformat(),
            "generation_mw": generation_mw,
            "percentages": percentages,
            "total_generation_mw": total_mw,
            "renewables_total_mw": renewables_mw,
            "renewables_percentage": renewables_pct,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def get_caiso_renewable_generation(
    date: str | None = None,
    end: str | None = None,
    forecast_type: str = "actual",
) -> dict[str, Any]:
    """
    Get CAISO renewable (solar/wind) generation actuals or forecasts.
    
    Args:
        date: Date in YYYY-MM-DD format or "today"/"latest". Defaults to "latest".
        end: End date for range queries. Optional.
        forecast_type: One of "actual", "day_ahead", "hasp", "rtpd", "rtd"
    
    Returns:
        Dictionary with solar and wind generation data.
    """
    if date is None:
        date = "latest"
    
    try:
        if forecast_type == "actual":
            df = caiso.get_renewables_hourly(date=date, end=end)
        elif forecast_type == "day_ahead":
            df = caiso.get_renewables_forecast_dam(date=date, end=end)
        elif forecast_type == "hasp":
            df = caiso.get_renewables_forecast_hasp(date=date, end=end)
        elif forecast_type == "rtpd":
            df = caiso.get_renewables_forecast_rtpd(date=date, end=end)
        elif forecast_type == "rtd":
            df = caiso.get_renewables_forecast_rtd(date=date, end=end)
        else:
            return {"error": f"Invalid forecast_type: {forecast_type}"}
        
        if df.empty:
            return {"error": "No renewable data available", "date": date}
        
        # Filter to CAISO total
        df_total = df[df["Location"] == "CAISO"] if "Location" in df.columns else df
        
        if df_total.empty:
            df_total = df
        
        latest = df_total.iloc[-1]
        
        result = {
            "date": date,
            "forecast_type": forecast_type,
            "interval_start": latest["Interval Start"].isoformat(),
            "interval_end": latest["Interval End"].isoformat(),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Handle different column names between actual and forecast
        if "Solar" in latest:
            result["solar_mw"] = float(latest["Solar"]) if pd.notna(latest["Solar"]) else 0
        if "Wind" in latest:
            result["wind_mw"] = float(latest["Wind"]) if pd.notna(latest["Wind"]) else 0
        if "Solar MW" in latest:
            result["solar_mw"] = float(latest["Solar MW"]) if pd.notna(latest["Solar MW"]) else 0
        if "Wind MW" in latest:
            result["wind_mw"] = float(latest["Wind MW"]) if pd.notna(latest["Wind MW"]) else 0
        
        return result
    except Exception as e:
        return {"error": str(e), "date": date, "forecast_type": forecast_type}


def get_caiso_storage(
    date: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Get CAISO battery storage data in 5-minute intervals.
    Negative values = charging, Positive values = discharging.
    
    Args:
        date: Date in YYYY-MM-DD format or "today"/"latest". Defaults to "latest".
        end: End date for range queries. Optional.
    
    Returns:
        Dictionary with battery storage data.
    """
    if date is None:
        date = "latest"
    
    try:
        df = caiso.get_storage(date=date)
        
        if df.empty:
            return {"error": "No storage data available", "date": date}
        
        latest = df.iloc[-1]
        
        supply_mw = float(latest["Supply"])
        
        return {
            "date": date,
            "interval_start": latest["Interval Start"].isoformat(),
            "interval_end": latest["Interval End"].isoformat(),
            "total_batteries_mw": supply_mw,
            "stand_alone_batteries_mw": float(latest["Stand-alone Batteries"]),
            "hybrid_batteries_mw": float(latest["Hybrid Batteries"]),
            "status": "discharging" if supply_mw > 0 else "charging" if supply_mw < 0 else "idle",
            "daily_max_discharge_mw": float(df["Supply"].max()),
            "daily_max_charge_mw": float(df["Supply"].min()),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def get_caiso_net_demand(
    date: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Calculate CAISO net demand (total demand minus solar and wind).
    Net demand is critical for understanding duck curve dynamics.
    
    Args:
        date: Date in YYYY-MM-DD format or "today"/"latest". Defaults to "latest".
        end: End date for range queries. Optional.
    
    Returns:
        Dictionary with net demand analysis.
    """
    if date is None:
        date = "latest"
    
    try:
        # Get load and fuel mix
        load_df = caiso.get_load(date=date, end=end)
        fuel_df = caiso.get_fuel_mix(date=date, end=end)
        
        if load_df.empty or fuel_df.empty:
            return {"error": "Insufficient data for net demand calculation", "date": date}
        
        # Merge on Interval Start
        merged = pd.merge(
            load_df[["Interval Start", "Interval End", "Load"]],
            fuel_df[["Interval Start", "Solar", "Wind"]],
            on="Interval Start",
            how="inner"
        )
        
        if merged.empty:
            return {"error": "Could not merge load and fuel data", "date": date}
        
        # Calculate net demand
        merged["Net Demand"] = merged["Load"] - merged["Solar"] - merged["Wind"]
        
        latest = merged.iloc[-1]
        
        # Determine duck curve position based on time
        current_hour = latest["Interval Start"].hour
        if 6 <= current_hour < 10:
            duck_position = "morning_ramp"
        elif 10 <= current_hour < 16:
            duck_position = "belly"
        elif 16 <= current_hour < 21:
            duck_position = "evening_ramp"
        else:
            duck_position = "overnight"
        
        # Find expected net peak (max net demand for the day)
        net_peak_row = merged.loc[merged["Net Demand"].idxmax()]
        
        return {
            "date": date,
            "interval_start": latest["Interval Start"].isoformat(),
            "interval_end": latest["Interval End"].isoformat(),
            "current_demand_mw": float(latest["Load"]),
            "solar_mw": float(latest["Solar"]),
            "wind_mw": float(latest["Wind"]),
            "net_demand_mw": float(latest["Net Demand"]),
            "duck_curve_position": duck_position,
            "daily_net_peak_mw": float(merged["Net Demand"].max()),
            "daily_net_min_mw": float(merged["Net Demand"].min()),
            "net_peak_hour": net_peak_row["Interval Start"].hour,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def calculate_load_deviation(
    date: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Calculate deviation between Real-Time load and Day-Ahead forecast.
    This is the PRIMARY tool for answering "where is load deviating from forecast?"
    
    Args:
        date: Date in YYYY-MM-DD format or "today". Defaults to "today".
        end: End date for range queries. Optional.
    
    Returns:
        Dictionary with detailed deviation analysis including:
        - Hourly deviations in MW and percentage
        - Summary statistics
        - Pattern analysis (morning, midday, evening)
    """
    if date is None:
        date = "today"
    
    try:
        # Get actual hourly load
        actual_df = caiso.get_load_hourly(date=date, end=end)
        
        # Get day-ahead forecast
        forecast_df = caiso.get_load_forecast_day_ahead(date=date, end=end)
        
        if actual_df.empty or forecast_df.empty:
            return {"error": "Insufficient data for deviation calculation", "date": date}
        
        # Filter forecast to CA ISO-TAC total
        forecast_total = forecast_df[forecast_df["TAC Area Name"] == "CA ISO-TAC"].copy()
        actual_total = actual_df[actual_df["TAC Area Name"] == "CA ISO-TAC"].copy()
        
        if forecast_total.empty:
            forecast_total = forecast_df.copy()
        if actual_total.empty:
            actual_total = actual_df.copy()
        
        # Merge on Interval Start
        merged = pd.merge(
            actual_total[["Interval Start", "Interval End", "Load"]],
            forecast_total[["Interval Start", "Load Forecast"]],
            on="Interval Start",
            how="inner"
        )
        
        if merged.empty:
            return {"error": "Could not align actual and forecast data", "date": date}
        
        # Calculate deviations
        merged["Deviation MW"] = merged["Load"] - merged["Load Forecast"]
        merged["Deviation Pct"] = (merged["Deviation MW"] / merged["Load Forecast"]) * 100
        merged["Hour"] = merged["Interval Start"].dt.hour
        
        # Build hourly deviation list
        deviations = []
        for _, row in merged.iterrows():
            deviations.append({
                "hour_ending": int(row["Hour"]) + 1,
                "interval_start": row["Interval Start"].isoformat(),
                "da_forecast_mw": float(row["Load Forecast"]),
                "rt_actual_mw": float(row["Load"]),
                "deviation_mw": float(row["Deviation MW"]),
                "deviation_pct": round(float(row["Deviation Pct"]), 2),
                "significant": abs(row["Deviation MW"]) > 2000,
            })
        
        # Calculate summary
        mean_dev = merged["Deviation MW"].mean()
        
        # Pattern analysis by time of day
        morning = merged[(merged["Hour"] >= 6) & (merged["Hour"] < 10)]
        midday = merged[(merged["Hour"] >= 10) & (merged["Hour"] < 16)]
        evening = merged[(merged["Hour"] >= 16) & (merged["Hour"] < 21)]
        
        morning_avg = morning["Deviation MW"].mean() if not morning.empty else 0
        midday_avg = midday["Deviation MW"].mean() if not midday.empty else 0
        evening_avg = evening["Deviation MW"].mean() if not evening.empty else 0
        
        # Determine likely driver based on pattern
        drivers = []
        
        # Check for consistent direction across all periods (suggests temperature)
        if (morning_avg < -500 and evening_avg < -500) or (morning_avg > 500 and evening_avg > 500):
            if mean_dev < 0:
                drivers.append({
                    "driver": "temperature",
                    "detail": "Load running below forecast - likely warmer than expected (reduced heating)",
                    "confidence": "high"
                })
            else:
                drivers.append({
                    "driver": "temperature", 
                    "detail": "Load running above forecast - likely colder than expected (increased heating)",
                    "confidence": "high"
                })
        
        # Check for midday-specific deviation (suggests solar/BTM)
        if abs(midday_avg) > 1500 and abs(morning_avg) < 500:
            drivers.append({
                "driver": "behind_the_meter_solar",
                "detail": "Midday deviation suggests BTM solar generation different than forecast",
                "confidence": "medium"
            })
        
        # Check if it's a weekend or holiday
        if not merged.empty:
            sample_date = merged.iloc[0]["Interval Start"]
            if sample_date.weekday() >= 5:
                drivers.append({
                    "driver": "calendar",
                    "detail": "Weekend - reduced commercial/industrial load",
                    "confidence": "high"
                })
        
        if not drivers:
            drivers.append({
                "driver": "unknown",
                "detail": "Pattern does not match typical drivers",
                "confidence": "low"
            })
        
        return {
            "date": date,
            "analysis_timestamp": datetime.now().isoformat(),
            "deviations": deviations,
            "summary": {
                "mean_deviation_mw": round(mean_dev, 1),
                "max_deviation_mw": round(float(merged["Deviation MW"].max()), 1),
                "min_deviation_mw": round(float(merged["Deviation MW"].min()), 1),
                "hours_analyzed": len(merged),
                "hours_with_significant_deviation": sum(1 for d in deviations if d["significant"]),
                "overall_direction": "RT > DA (load above forecast)" if mean_dev > 0 else "RT < DA (load below forecast)",
            },
            "driver_analysis": {
                "likely_drivers": drivers,
                "pattern": {
                    "morning_avg_deviation_mw": round(morning_avg, 0),
                    "midday_avg_deviation_mw": round(midday_avg, 0),
                    "evening_avg_deviation_mw": round(evening_avg, 0),
                }
            }
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def get_caiso_curtailment(
    date: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Get CAISO solar and wind curtailment data.
    
    Args:
        date: Date in YYYY-MM-DD format or "latest". Defaults to "latest".
        end: End date for range queries. Optional.
    
    Returns:
        Dictionary with curtailment volumes by fuel type and reason.
    """
    if date is None:
        date = "latest"
    
    try:
        df = caiso.get_curtailment(date=date, end=end)
        
        if df.empty:
            return {"error": "No curtailment data available", "date": date}
        
        # Aggregate by fuel type
        solar_mwh = df[df["Fuel Type"] == "Solar"]["Curtailment MWH"].sum()
        wind_mwh = df[df["Fuel Type"] == "Wind"]["Curtailment MWH"].sum()
        total_mwh = solar_mwh + wind_mwh
        
        # Get max curtailment MW
        solar_max_mw = df[df["Fuel Type"] == "Solar"]["Curtailment MW"].max()
        wind_max_mw = df[df["Fuel Type"] == "Wind"]["Curtailment MW"].max()
        
        # Group by reason
        by_reason = df.groupby("Curtailment Reason")["Curtailment MWH"].sum().to_dict()
        
        return {
            "date": date,
            "solar_curtailment_mwh": float(solar_mwh) if pd.notna(solar_mwh) else 0,
            "wind_curtailment_mwh": float(wind_mwh) if pd.notna(wind_mwh) else 0,
            "total_curtailment_mwh": float(total_mwh) if pd.notna(total_mwh) else 0,
            "solar_max_curtailment_mw": float(solar_max_mw) if pd.notna(solar_max_mw) else 0,
            "wind_max_curtailment_mw": float(wind_max_mw) if pd.notna(wind_max_mw) else 0,
            "curtailment_by_reason": by_reason,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def get_caiso_tie_flows(
    date: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Get CAISO real-time intertie (transmission) flow data.
    Positive = export, Negative = import.
    
    Args:
        date: Date in YYYY-MM-DD format or "latest". Defaults to "latest".
        end: End date for range queries. Optional.
    
    Returns:
        Dictionary with tie flow data by interface.
    """
    if date is None:
        date = "latest"
    
    try:
        df = caiso.get_tie_flows_real_time(date=date, end=end)
        
        if df.empty:
            return {"error": "No tie flow data available", "date": date}
        
        # Get latest values for each interface
        latest_time = df["Interval Start"].max()
        latest_df = df[df["Interval Start"] == latest_time]
        
        # Calculate net imports
        net_flow = latest_df["MW"].sum()
        
        # Build interface list
        interfaces = []
        for _, row in latest_df.iterrows():
            interfaces.append({
                "interface_id": row["Interface ID"],
                "tie_name": row["Tie Name"],
                "from_baa": row["From BAA"],
                "to_baa": row["To BAA"],
                "flow_mw": float(row["MW"]),
                "direction": "import" if row["MW"] < 0 else "export",
            })
        
        return {
            "date": date,
            "interval_start": latest_time.isoformat(),
            "net_interchange_mw": float(net_flow),
            "net_direction": "net_import" if net_flow < 0 else "net_export",
            "interfaces": interfaces,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def get_caiso_as_prices(
    date: str | None = None,
    end: str | None = None,
    market: str = "DAM",
) -> dict[str, Any]:
    """
    Get CAISO Ancillary Services prices by region.
    
    Args:
        date: Date in YYYY-MM-DD format or "today". Defaults to "today".
        end: End date for range queries. Optional.
        market: "DAM" or "HASP". Defaults to "DAM".
    
    Returns:
        Dictionary with AS prices by service type and region.
    """
    if date is None:
        date = "today"
    
    try:
        df = caiso.get_as_prices(date=date, end=end, market=market)
        
        if df.empty:
            return {"error": "No AS price data available", "date": date}
        
        # Get latest prices
        latest_time = df["Interval Start"].max()
        latest_df = df[df["Interval Start"] == latest_time]
        
        # Build price structure by region
        prices_by_region = {}
        for _, row in latest_df.iterrows():
            region = row["Region"]
            prices_by_region[region] = {
                "regulation_up": float(row.get("Regulation Up", 0)),
                "regulation_down": float(row.get("Regulation Down", 0)),
                "spinning_reserves": float(row.get("Spinning Reserves", 0)),
                "non_spinning_reserves": float(row.get("Non-Spinning Reserves", 0)),
                "regulation_mileage_up": float(row.get("Regulation Mileage Up", 0)),
                "regulation_mileage_down": float(row.get("Regulation Mileage Down", 0)),
            }
        
        return {
            "date": date,
            "market": market,
            "interval_start": latest_time.isoformat(),
            "prices_by_region": prices_by_region,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date, "market": market}


def get_caiso_shadow_prices(
    date: str | None = None,
    end: str | None = None,
    market: str = "DAM",
) -> dict[str, Any]:
    """
    Get CAISO transmission constraint shadow prices.
    Shadow prices indicate congestion costs on specific transmission paths.
    
    Args:
        date: Date in YYYY-MM-DD format or "today"/"latest". Defaults to "latest".
        end: End date for range queries. Optional.
        market: "DAM", "HASP", or "RTM". Defaults to "DAM".
    
    Returns:
        Dictionary with constraint shadow prices.
    """
    if date is None:
        date = "latest"
    
    try:
        if market == "DAM":
            df = caiso.get_nomogram_branch_shadow_prices_day_ahead_hourly(date=date, end=end)
        elif market == "HASP":
            df = caiso.get_nomogram_branch_shadow_prices_hasp_hourly(date=date, end=end)
        elif market == "RTM":
            df = caiso.get_nomogram_branch_shadow_price_forecast_15_min(date=date, end=end)
        else:
            return {"error": f"Invalid market: {market}"}
        
        if df.empty:
            return {"error": "No shadow price data available", "date": date}
        
        # Get binding constraints (non-zero prices)
        latest_time = df["Interval Start"].max()
        latest_df = df[df["Interval Start"] == latest_time]
        binding = latest_df[latest_df["Price"] != 0]
        
        constraints = []
        for _, row in binding.iterrows():
            constraints.append({
                "location": row["Location"],
                "shadow_price": float(row["Price"]),
                "constraint_cause": row.get("Constraint Cause", "Unknown"),
            })
        
        return {
            "date": date,
            "market": market,
            "interval_start": latest_time.isoformat(),
            "binding_constraints_count": len(constraints),
            "binding_constraints": constraints,
            "total_congestion_cost": sum(c["shadow_price"] for c in constraints),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date, "market": market}


def get_caiso_outages(
    date: str | None = None,
) -> dict[str, Any]:
    """
    Get CAISO curtailed and non-operational generator outage report.
    
    Args:
        date: Date in YYYY-MM-DD format. Defaults to yesterday (latest available).
    
    Returns:
        Dictionary with outage information.
    """
    if date is None:
        # Data is typically available for previous day
        date = (pd.Timestamp.now(tz="US/Pacific") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        df = caiso.get_curtailed_non_operational_generator_report(date=date)
        
        if df.empty:
            return {"error": "No outage data available", "date": date}
        
        # Calculate totals
        total_curtailed_mw = df["Curtailment MW"].sum()
        
        # Group by outage type
        by_type = df.groupby("Outage Type")["Curtailment MW"].sum().to_dict()
        
        # Build outage list
        outages = []
        for _, row in df.iterrows():
            outages.append({
                "resource_name": row["Resource Name"],
                "resource_id": row["Resource ID"],
                "outage_type": row["Outage Type"],
                "nature_of_work": row["Nature of Work"],
                "curtailment_mw": float(row["Curtailment MW"]),
                "pmax_mw": float(row["Resource PMAX MW"]),
                "start_time": row["Curtailment Start Time"].isoformat() if pd.notna(row["Curtailment Start Time"]) else None,
                "end_time": row["Curtailment End Time"].isoformat() if pd.notna(row["Curtailment End Time"]) else None,
            })
        
        return {
            "date": date,
            "total_curtailed_mw": float(total_curtailed_mw),
            "outages_by_type": by_type,
            "outage_count": len(outages),
            "outages": outages[:20],  # Limit to first 20 for readability
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "date": date}


def get_caiso_grid_status() -> dict[str, Any]:
    """
    Get current CAISO grid status.
    
    Returns:
        Dictionary with grid status (Normal, Restricted Maintenance, Flex Alert, etc.)
    """
    try:
        status = caiso.get_status(date="latest")
        
        return {
            "status": status.status,
            "time": status.time.isoformat(),
            "reserves": status.reserves,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}