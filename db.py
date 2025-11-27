import duckdb

# Connect to an in-memory database
con = duckdb.connect()

# Load the data from CSV
# We use read_csv_auto to infer types, but we can also specify types if needed based on the user's list
con.execute("CREATE TABLE grid_data AS SELECT * FROM read_csv_auto('data/data.csv')")

print("=== Data Overview ===")
con.sql("DESCRIBE grid_data").show()

# 1. Identify the Top Price Spikes
# This helps visualize the most extreme events in the dataset
print("\n=== Top 10 Price Spikes ===")
con.sql("""
    SELECT 
        timestamp, 
        price_mwh, 
        temperature_2m, 
        cloud_cover, 
        wind_speed_10m,
        hour,
        day_of_week
    FROM grid_data 
    ORDER BY price_mwh DESC 
    LIMIT 10
""").show()

# 2. Weather Correlation Analysis
# Compare average weather conditions during price spikes (> 95th percentile) vs normal operation
# This helps understand "which weather parameters might have caused them"
print("\n=== Weather Conditions: High Price (>95th percentile) vs Normal ===")
con.sql("""
    WITH stats AS (
        SELECT quantile_cont(price_mwh, 0.95) as p95 FROM grid_data
    )
    SELECT 
        CASE 
            WHEN price_mwh > (SELECT p95 FROM stats) THEN 'Spike (>95%)' 
            ELSE 'Normal' 
        END as category,
        COUNT(*) as hours_count,
        ROUND(AVG(price_mwh), 2) as avg_price,
        ROUND(AVG(temperature_2m), 2) as avg_temp_c,
        ROUND(AVG(cloud_cover), 2) as avg_cloud_cover,
        ROUND(AVG(wind_speed_10m), 2) as avg_wind_speed,
        ROUND(AVG(relative_humidity_2m), 2) as avg_humidity
    FROM grid_data
    GROUP BY 1
    ORDER BY avg_price DESC
""").show()

# 3. Find Similar Historical Spikes (Nearest Neighbors by Weather)
# Take the highest price spike, and find other timestamps with very similar weather conditions
# to see if they also resulted in high prices.
print("\n=== Historical Days with Similar Weather to the Max Spike ===")
con.sql("""
    WITH max_spike AS (
        SELECT * FROM grid_data ORDER BY price_mwh DESC LIMIT 1
    )
    SELECT 
        t.timestamp,
        t.price_mwh,
        t.temperature_2m,
        t.cloud_cover,
        t.wind_speed_10m,
        -- Calculate a simple similarity score (lower is more similar)
        -- We weight temperature and cloud cover as likely drivers
        (ABS(t.temperature_2m - m.temperature_2m) * 2 + 
         ABS(t.cloud_cover - m.cloud_cover) + 
         ABS(t.wind_speed_10m - m.wind_speed_10m)) as similarity_score
    FROM grid_data t, max_spike m
    WHERE t.timestamp != m.timestamp
    ORDER BY similarity_score ASC
    LIMIT 10
""").show()
