import gridstatus

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