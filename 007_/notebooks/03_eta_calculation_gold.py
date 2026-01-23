"""
ETA Calculation & Risk Scoring - Gold Layer
=============================================
This notebook calculates ETA, congestion index, and risk scores.

Author: Data Analysis Team
Created: 2026-01-23
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
SILVER_PATH = "../data/silver/"
GOLD_PATH = "../data/gold/"

# ============================================================================
# 1. ETA Calculation
# ============================================================================

def calculate_eta(df):
    """
    Calculate Estimated Time of Arrival

    Formula: ETA (hours) = Distance (nautical miles) / Speed (knots)

    Parameters:
    -----------
    df : pd.DataFrame
        Vessel data with distance and speed

    Returns:
    --------
    pd.DataFrame : Data with ETA calculations
    """
    # Use 30-minute average speed for more stable estimates
    df['Calculated_ETA_Hours'] = df['Distance_to_Dest_nm'] / df['Speed_30min_avg']

    # Calculate ETA datetime
    df['Calculated_ETA_DateTime'] = pd.to_datetime(df['Timestamp_UTC']) + \
                                      pd.to_timedelta(df['Calculated_ETA_Hours'], unit='h')

    # Handle division by zero or very low speeds
    df.loc[df['Speed_30min_avg'] < 1, 'Calculated_ETA_Hours'] = np.nan
    df.loc[df['Speed_30min_avg'] < 1, 'Calculated_ETA_DateTime'] = pd.NaT

    print(f"✅ Calculated ETA for {len(df)} vessels")

    return df


# ============================================================================
# 2. Risk Scoring
# ============================================================================

def calculate_delay_risk_score(df, congestion_df=None):
    """
    Calculate delay risk score based on multiple factors

    Risk Score = (Speed_Volatility * 0.4) + (Congestion_Index * 0.4) + (Weather_Factor * 0.2)

    Parameters:
    -----------
    df : pd.DataFrame
        Vessel data with speed volatility
    congestion_df : pd.DataFrame
        Port congestion data (optional)

    Returns:
    --------
    pd.DataFrame : Data with risk scores
    """
    # Normalize speed volatility to 0-100 scale
    speed_risk = df['Speed_Volatility'] * 100 * 0.4

    # Congestion risk (if available)
    if congestion_df is not None:
        # Merge congestion data
        congestion_map = congestion_df.set_index('Port_Name')['Congestion_Index'].to_dict()
        df['Port_Congestion_Index'] = df['Destination_Port'].map(congestion_map).fillna(0)
        congestion_risk = df['Port_Congestion_Index'] * 20 * 0.4  # Scale to 0-100
    else:
        congestion_risk = 0

    # Weather factor (placeholder - would integrate weather API in production)
    weather_risk = np.random.uniform(0, 20, len(df)) * 0.2  # Simulated

    # Total risk score
    df['Delay_Risk_Score'] = speed_risk + congestion_risk + weather_risk

    # Categorize risk
    df['Risk_Category'] = pd.cut(df['Delay_Risk_Score'],
                                   bins=[0, 30, 60, 100],
                                   labels=['Low', 'Medium', 'High'])

    print(f"✅ Calculated risk scores")
    print(f"   Low Risk: {(df['Risk_Category'] == 'Low').sum()}")
    print(f"   Medium Risk: {(df['Risk_Category'] == 'Medium').sum()}")
    print(f"   High Risk: {(df['Risk_Category'] == 'High').sum()}")

    return df


# ============================================================================
# 3. Congestion Index Calculation
# ============================================================================

def calculate_congestion_index(vessel_df, dock_df):
    """
    Calculate port congestion index

    Congestion Index = Waiting vessels / Available berths

    Parameters:
    -----------
    vessel_df : pd.DataFrame
        Vessel data
    dock_df : pd.DataFrame
        Dock status data

    Returns:
    --------
    pd.DataFrame : Congestion index by port
    """
    # Count vessels heading to each port within 24 hours
    vessels_24h = vessel_df[vessel_df['Calculated_ETA_Hours'] <= 24].copy()
    incoming_count = vessels_24h.groupby('Destination_Port').size().reset_index(name='Vessels_24h_Incoming')

    # Calculate congestion for each port
    congestion_list = []

    for _, dock in dock_df.iterrows():
        port_name = dock['Port_Name']

        # Simulate occupancy (in production, this would be real-time data)
        occupied = np.random.randint(0, dock['Berth_Count'] + 1)
        available = dock['Berth_Count'] - occupied

        # Get incoming vessels
        incoming = incoming_count[incoming_count['Destination_Port'] == port_name]
        incoming_vessels = incoming['Vessels_24h_Incoming'].values[0] if len(incoming) > 0 else 0

        # Calculate congestion index
        if available > 0:
            congestion_idx = incoming_vessels / available
        else:
            congestion_idx = 999  # Critical - no berths available

        # Determine congestion level
        if congestion_idx < 0.5:
            level = 'Normal'
        elif congestion_idx < 1.0:
            level = 'Moderate'
        elif congestion_idx < 2.0:
            level = 'High'
        else:
            level = 'Critical'

        congestion_list.append({
            'Port_Name': port_name,
            'Country': dock['Country'],
            'Total_Berths': dock['Berth_Count'],
            'Occupied_Berths': occupied,
            'Waiting_Vessels': 0,  # Would come from queue data
            'Congestion_Index': congestion_idx,
            'Congestion_Level': level,
            'Avg_Wait_Hours': congestion_idx * 2,  # Simplified estimate
            'Vessels_24h_Incoming': incoming_vessels,
            'Timestamp': datetime.utcnow()
        })

    congestion_df = pd.DataFrame(congestion_list)

    print(f"✅ Calculated congestion for {len(congestion_df)} ports")
    print(congestion_df[['Port_Name', 'Congestion_Index', 'Congestion_Level']])

    return congestion_df


# ============================================================================
# 4. Create Gold Layer Tables
# ============================================================================

def create_eta_table(df):
    """
    Create final ETA table for Power BI

    Parameters:
    -----------
    df : pd.DataFrame
        Processed vessel data

    Returns:
    --------
    pd.DataFrame : ETA table
    """
    eta_columns = [
        'Vessel_ID', 'Vessel_Name', 'Vessel_Type',
        'Latitude', 'Longitude',
        'Destination_Port',
        'Distance_to_Dest_km', 'Distance_to_Dest_nm',
        'Speed_knots', 'Speed_30min_avg',
        'Calculated_ETA_Hours', 'Calculated_ETA_DateTime',
        'Speed_Volatility', 'Delay_Risk_Score', 'Risk_Category',
        'Timestamp_UTC'
    ]

    # Rename for clarity
    eta_table = df[eta_columns].copy()
    eta_table = eta_table.rename(columns={
        'Latitude': 'Current_Latitude',
        'Longitude': 'Current_Longitude',
        'Timestamp_UTC': 'Last_Updated'
    })

    return eta_table


def create_vessel_snapshot(df):
    """
    Create live vessel snapshot for real-time dashboard

    Parameters:
    -----------
    df : pd.DataFrame
        Processed vessel data

    Returns:
    --------
    pd.DataFrame : Vessel snapshot
    """
    snapshot_columns = [
        'Vessel_ID', 'Vessel_Name', 'Vessel_Type',
        'Latitude', 'Longitude',
        'Speed_knots', 'Heading',
        'Destination_Port',
        'Calculated_ETA_Hours', 'Calculated_ETA_DateTime',
        'Distance_to_Dest_km',
        'Delay_Risk_Score',
        'Timestamp_UTC'
    ]

    snapshot = df[snapshot_columns].copy()

    # Add status based on speed
    snapshot['Status'] = snapshot['Speed_knots'].apply(
        lambda x: 'Underway' if x > 1 else 'Moored/Anchored'
    )

    snapshot = snapshot.rename(columns={
        'Calculated_ETA_Hours': 'ETA_Hours',
        'Calculated_ETA_DateTime': 'ETA_DateTime',
        'Delay_Risk_Score': 'Risk_Score',
        'Timestamp_UTC': 'Last_Updated'
    })

    return snapshot


# ============================================================================
# 5. Main Gold Layer Pipeline
# ============================================================================

def process_to_gold(silver_file, dock_file):
    """
    Main pipeline: Silver → Gold

    Parameters:
    -----------
    silver_file : str
        Path to silver layer vessel data
    dock_file : str
        Path to dock master data

    Returns:
    --------
    tuple : (eta_table, congestion_table, snapshot_table)
    """
    print("=" * 70)
    print("ETA Calculation & Risk Scoring - Gold Layer")
    print("=" * 70)

    # Load data
    print("\n📂 Loading silver layer data...")
    vessel_df = pd.read_csv(silver_file)
    dock_df = pd.read_csv(f"../data/bronze/{dock_file}")

    print(f"Loaded {len(vessel_df)} vessel records")

    # Step 1: Calculate ETA
    print("\n⏰ Calculating ETA...")
    vessel_df = calculate_eta(vessel_df)

    # Step 2: Calculate congestion index
    print("\n🚦 Calculating port congestion...")
    congestion_df = calculate_congestion_index(vessel_df, dock_df)

    # Step 3: Calculate risk scores
    print("\n⚠️ Calculating delay risk scores...")
    vessel_df = calculate_delay_risk_score(vessel_df, congestion_df)

    # Step 4: Create gold tables
    print("\n📊 Creating gold layer tables...")
    eta_table = create_eta_table(vessel_df)
    snapshot_table = create_vessel_snapshot(vessel_df)

    # Save to gold layer
    timestamp = datetime.utcnow().strftime('%Y%m%d')

    eta_file = f"{GOLD_PATH}ETA_Table_{timestamp}.csv"
    congestion_file = f"{GOLD_PATH}Congestion_Index_{timestamp}.csv"
    snapshot_file = f"{GOLD_PATH}Vessel_Live_Snapshot_Latest.csv"

    eta_table.to_csv(eta_file, index=False)
    congestion_df.to_csv(congestion_file, index=False)
    snapshot_table.to_csv(snapshot_file, index=False)

    print(f"\n✅ Saved ETA table: {eta_file}")
    print(f"✅ Saved Congestion table: {congestion_file}")
    print(f"✅ Saved Snapshot table: {snapshot_file}")

    return eta_table, congestion_df, snapshot_table


# ============================================================================
# 6. Execution
# ============================================================================

if __name__ == "__main__":
    # Adjust file paths as needed
    silver_file = f"{SILVER_PATH}Vessel_Processed_20260123.csv"
    dock_file = "Dock_Master_20260123.csv"

    eta_df, congestion_df, snapshot_df = process_to_gold(silver_file, dock_file)

    print("\n" + "=" * 70)
    print("Summary Statistics")
    print("=" * 70)
    print(f"\nTotal vessels tracked: {len(snapshot_df)}")
    print(f"Vessels arriving within 24h: {(eta_df['Calculated_ETA_Hours'] <= 24).sum()}")
    print(f"\nAverage ETA: {eta_df['Calculated_ETA_Hours'].mean():.2f} hours")
    print(f"Average Risk Score: {eta_df['Delay_Risk_Score'].mean():.2f}")

    print("\n🎯 Gold layer processing complete!")
