"""
Data Ingestion - Bronze Layer
=================================
This notebook handles the ingestion of raw AIS vessel data and dock master data.

Author: Data Analysis Team
Created: 2026-01-23
"""

import pandas as pd
import numpy as np
from datetime import datetime
import requests
import json

# Configuration
DATA_PATH = "../data/bronze/"
AIS_API_URL = "YOUR_AIS_API_ENDPOINT"  # Replace with actual AIS API
API_KEY = "YOUR_API_KEY"  # Store securely

# ============================================================================
# 1. AIS Vessel Data Ingestion
# ============================================================================

def fetch_ais_data(vessel_types=['LNG', 'LPG']):
    """
    Fetch real-time AIS data from API

    Parameters:
    -----------
    vessel_types : list
        Types of vessels to fetch (LNG, LPG)

    Returns:
    --------
    pd.DataFrame : Raw AIS data
    """

    # Example API call (adjust based on your AIS provider)
    # headers = {'Authorization': f'Bearer {API_KEY}'}
    # params = {'vessel_types': ','.join(vessel_types)}
    # response = requests.get(AIS_API_URL, headers=headers, params=params)

    # For demo purposes, create sample data
    sample_data = {
        'Vessel_ID': ['477123456', '477654321', '477987654'],
        'Vessel_Name': ['LNG EXPLORER', 'LPG CARRIER 1', 'LNG SPIRIT'],
        'Vessel_Type': ['LNG', 'LPG', 'LNG'],
        'Latitude': [37.7749, 35.1028, 51.5074],
        'Longitude': [-122.4194, 129.0403, -0.1278],
        'Speed_knots': [15.3, 12.8, 14.5],
        'Heading': [235.5, 180.0, 90.0],
        'Timestamp': [datetime.utcnow()] * 3,
        'Destination_Port': ['BUSAN', 'SINGAPORE', 'ROTTERDAM'],
        'Draft': [11.5, 10.2, 12.0],
        'IMO_Number': ['IMO9876543', 'IMO9876544', 'IMO9876545']
    }

    df = pd.DataFrame(sample_data)
    return df


def save_ais_bronze(df, timestamp=None):
    """
    Save AIS data to bronze layer

    Parameters:
    -----------
    df : pd.DataFrame
        AIS data
    timestamp : str
        Optional timestamp for filename
    """
    if timestamp is None:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    filename = f"{DATA_PATH}AIS_Vessel_Raw_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} records to {filename}")
    return filename


# ============================================================================
# 2. Dock Master Data Ingestion
# ============================================================================

def load_dock_master():
    """
    Load or create dock master data

    Returns:
    --------
    pd.DataFrame : Dock master reference data
    """

    # Sample dock data (replace with actual data source)
    dock_data = {
        'Dock_ID': ['BUSAN_LNG_D1', 'SINGAPORE_LNG_D1', 'ROTTERDAM_LNG_D1'],
        'Port_Name': ['Busan Port', 'Singapore Port', 'Rotterdam Port'],
        'Country': ['KR', 'SG', 'NL'],
        'Latitude': [35.1028, 1.2644, 51.9244],
        'Longitude': [129.0403, 103.8215, 4.4777],
        'Berth_Count': [3, 5, 4],
        'Max_Vessel_LOA': [300.0, 320.0, 310.0],
        'Terminal_Type': ['LNG', 'LNG', 'LNG'],
        'Operator': ['Korea Gas Corp', 'Singapore LNG', 'Gate Terminal']
    }

    df = pd.DataFrame(dock_data)
    return df


def save_dock_master(df):
    """
    Save dock master data to bronze layer
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    filename = f"{DATA_PATH}Dock_Master_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved dock master data to {filename}")
    return filename


# ============================================================================
# 3. Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Data Ingestion - Bronze Layer")
    print("=" * 70)

    # Fetch AIS data
    print("\n📡 Fetching AIS vessel data...")
    ais_df = fetch_ais_data()
    print(f"Retrieved {len(ais_df)} vessel records")
    print(ais_df.head())

    # Save to bronze layer
    ais_file = save_ais_bronze(ais_df)

    # Load dock master
    print("\n📍 Loading dock master data...")
    dock_df = load_dock_master()
    print(f"Loaded {len(dock_df)} dock records")
    print(dock_df.head())

    # Save dock master
    dock_file = save_dock_master(dock_df)

    print("\n✅ Bronze layer ingestion complete!")
