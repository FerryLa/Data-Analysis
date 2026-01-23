"""
Data Processing - Silver Layer
=================================
This notebook processes raw AIS data, validates, and calculates distance metrics.

Author: Data Analysis Team
Created: 2026-01-23
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

# Configuration
BRONZE_PATH = "../data/bronze/"
SILVER_PATH = "../data/silver/"

# ============================================================================
# 1. Haversine Distance Calculation
# ============================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    Parameters:
    -----------
    lat1, lon1 : float
        Coordinates of point 1
    lat2, lon2 : float
        Coordinates of point 2

    Returns:
    --------
    float : Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def km_to_nautical_miles(km):
    """Convert kilometers to nautical miles"""
    return km * 0.539957


# ============================================================================
# 2. Data Validation & Cleaning
# ============================================================================

def validate_coordinates(df):
    """
    Validate latitude and longitude ranges

    Parameters:
    -----------
    df : pd.DataFrame
        Vessel data with Latitude and Longitude

    Returns:
    --------
    pd.DataFrame : Validated data
    """
    print(f"Initial records: {len(df)}")

    # Valid ranges
    valid_lat = (df['Latitude'] >= -90) & (df['Latitude'] <= 90)
    valid_lon = (df['Longitude'] >= -180) & (df['Longitude'] <= 180)

    df_valid = df[valid_lat & valid_lon].copy()

    print(f"After coordinate validation: {len(df_valid)}")
    print(f"Removed {len(df) - len(df_valid)} invalid records")

    return df_valid


def validate_speed(df, max_speed=30):
    """
    Validate speed values

    Parameters:
    -----------
    df : pd.DataFrame
        Vessel data
    max_speed : float
        Maximum reasonable speed in knots

    Returns:
    --------
    pd.DataFrame : Validated data
    """
    initial_count = len(df)

    # Remove negative speeds and unrealistic high speeds
    df_valid = df[(df['Speed_knots'] >= 0) & (df['Speed_knots'] <= max_speed)].copy()

    print(f"After speed validation: {len(df_valid)}")
    print(f"Removed {initial_count - len(df_valid)} records with invalid speed")

    return df_valid


def filter_vessel_types(df, vessel_types=['LNG', 'LPG']):
    """
    Filter only relevant vessel types

    Parameters:
    -----------
    df : pd.DataFrame
        Vessel data
    vessel_types : list
        List of vessel types to keep

    Returns:
    --------
    pd.DataFrame : Filtered data
    """
    df_filtered = df[df['Vessel_Type'].isin(vessel_types)].copy()
    print(f"Filtered to {len(df_filtered)} {'/'.join(vessel_types)} vessels")

    return df_filtered


# ============================================================================
# 3. Distance Calculation
# ============================================================================

def calculate_distance_to_destination(vessel_df, dock_df):
    """
    Calculate distance from each vessel to its destination dock

    Parameters:
    -----------
    vessel_df : pd.DataFrame
        Vessel data with current position
    dock_df : pd.DataFrame
        Dock master data

    Returns:
    --------
    pd.DataFrame : Vessel data with distance columns
    """
    # Create a mapping of port names to dock coordinates
    dock_mapping = dock_df.set_index('Port_Name')[['Latitude', 'Longitude']].to_dict('index')

    # Calculate distance for each vessel
    distances_km = []
    distances_nm = []

    for idx, row in vessel_df.iterrows():
        dest_port = row['Destination_Port']

        if dest_port in dock_mapping:
            dock_lat = dock_mapping[dest_port]['Latitude']
            dock_lon = dock_mapping[dest_port]['Longitude']

            dist_km = haversine_distance(
                row['Latitude'], row['Longitude'],
                dock_lat, dock_lon
            )
            dist_nm = km_to_nautical_miles(dist_km)
        else:
            # If destination not found, set to NaN
            dist_km = np.nan
            dist_nm = np.nan

        distances_km.append(dist_km)
        distances_nm.append(dist_nm)

    vessel_df['Distance_to_Dest_km'] = distances_km
    vessel_df['Distance_to_Dest_nm'] = distances_nm

    return vessel_df


# ============================================================================
# 4. Speed Statistics
# ============================================================================

def calculate_speed_statistics(df):
    """
    Calculate rolling speed statistics (30-minute window simulation)

    Note: In real-time implementation, this would use actual historical data

    Parameters:
    -----------
    df : pd.DataFrame
        Vessel data

    Returns:
    --------
    pd.DataFrame : Data with speed statistics
    """
    # For demo purposes, add some random variation
    # In production, this would be calculated from historical speed data

    df['Speed_30min_avg'] = df['Speed_knots'] * np.random.uniform(0.95, 1.05, len(df))
    df['Speed_Volatility'] = np.abs(df['Speed_knots'] - df['Speed_30min_avg']) / df['Speed_knots']

    return df


# ============================================================================
# 5. Additional Features
# ============================================================================

def add_derived_features(df):
    """
    Add derived features for analysis

    Parameters:
    -----------
    df : pd.DataFrame
        Vessel data

    Returns:
    --------
    pd.DataFrame : Enhanced data
    """
    # Is vessel moving?
    df['Is_Moving'] = df['Speed_knots'] > 1.0

    # Standardize timestamp to UTC
    df['Timestamp_UTC'] = pd.to_datetime(df['Timestamp'], utc=True)

    return df


# ============================================================================
# 6. Main Processing Pipeline
# ============================================================================

def process_to_silver(ais_file, dock_file):
    """
    Main processing pipeline: Bronze → Silver

    Parameters:
    -----------
    ais_file : str
        Path to AIS bronze data
    dock_file : str
        Path to dock master data

    Returns:
    --------
    pd.DataFrame : Processed silver layer data
    """
    print("=" * 70)
    print("Data Processing - Silver Layer")
    print("=" * 70)

    # Load bronze data
    print("\n📂 Loading bronze layer data...")
    vessel_df = pd.read_csv(ais_file)
    dock_df = pd.read_csv(dock_file)

    print(f"Loaded {len(vessel_df)} vessel records")
    print(f"Loaded {len(dock_df)} dock records")

    # Step 1: Validate coordinates
    print("\n🔍 Validating coordinates...")
    vessel_df = validate_coordinates(vessel_df)

    # Step 2: Validate speed
    print("\n🔍 Validating speed...")
    vessel_df = validate_speed(vessel_df)

    # Step 3: Filter vessel types
    print("\n🚢 Filtering vessel types...")
    vessel_df = filter_vessel_types(vessel_df)

    # Step 4: Calculate distances
    print("\n📏 Calculating distances to destinations...")
    vessel_df = calculate_distance_to_destination(vessel_df, dock_df)

    # Step 5: Calculate speed statistics
    print("\n📊 Calculating speed statistics...")
    vessel_df = calculate_speed_statistics(vessel_df)

    # Step 6: Add derived features
    print("\n➕ Adding derived features...")
    vessel_df = add_derived_features(vessel_df)

    # Save to silver layer
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    output_file = f"{SILVER_PATH}Vessel_Processed_{timestamp}.csv"
    vessel_df.to_csv(output_file, index=False)

    print(f"\n✅ Saved {len(vessel_df)} processed records to {output_file}")

    return vessel_df


# ============================================================================
# 7. Execution
# ============================================================================

if __name__ == "__main__":
    # Example usage - adjust file paths as needed
    latest_ais = f"{BRONZE_PATH}AIS_Vessel_Raw_20260123_143000.csv"
    latest_dock = f"{BRONZE_PATH}Dock_Master_20260123.csv"

    processed_df = process_to_silver(latest_ais, latest_dock)

    print("\n📋 Sample processed data:")
    print(processed_df[['Vessel_ID', 'Vessel_Type', 'Distance_to_Dest_km',
                        'Speed_knots', 'Speed_30min_avg']].head())
