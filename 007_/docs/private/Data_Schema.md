# Data Schema Documentation

## Overview
This document defines the data structure for the Global Supply Chain Bottleneck & ETA Analysis System.

---

## Bronze Layer - Raw Data

### 1. AIS_Vessel_Raw
**Description**: Real-time vessel position data from AIS (Automatic Identification System)

| Column Name       | Data Type | Description                          | Example              |
|-------------------|-----------|--------------------------------------|----------------------|
| Vessel_ID         | string    | Unique vessel identifier (MMSI)      | "477123456"          |
| Vessel_Name       | string    | Name of the vessel                   | "LNG EXPLORER"       |
| Vessel_Type       | string    | Type of vessel (LNG/LPG)            | "LNG"                |
| Latitude          | float     | Current latitude (WGS84)             | 37.7749              |
| Longitude         | float     | Current longitude (WGS84)            | -122.4194            |
| Speed_knots       | float     | Speed over ground in knots           | 15.3                 |
| Heading           | float     | Vessel heading (0-360 degrees)       | 235.5                |
| Timestamp         | datetime  | Data collection timestamp (UTC)      | 2026-01-23 14:30:00  |
| Destination_Port  | string    | Reported destination port            | "BUSAN"              |
| Draft             | float     | Vessel draft in meters               | 11.5                 |
| IMO_Number        | string    | IMO vessel number                    | "IMO9876543"         |

**Data Source**: AIS API, Marine Traffic, VesselFinder
**Update Frequency**: Every 5-15 minutes
**Storage Format**: CSV, Parquet

---

### 2. Dock_Master
**Description**: Master data for LNG/LPG terminals and docking facilities

| Column Name       | Data Type | Description                          | Example              |
|-------------------|-----------|--------------------------------------|----------------------|
| Dock_ID           | string    | Unique dock identifier               | "BUSAN_LNG_D1"       |
| Port_Name         | string    | Name of the port                     | "Busan Port"         |
| Country           | string    | Country code                         | "KR"                 |
| Latitude          | float     | Dock latitude                        | 35.1028              |
| Longitude         | float     | Dock longitude                       | 129.0403             |
| Berth_Count       | int       | Total number of berths               | 3                    |
| Max_Vessel_LOA    | float     | Maximum vessel length (meters)       | 300.0                |
| Terminal_Type     | string    | LNG or LPG terminal                  | "LNG"                |
| Operator          | string    | Terminal operator name               | "Korea Gas Corp"     |

**Data Source**: Static reference data, Port authorities
**Update Frequency**: Monthly or as needed

---

### 3. Port_Queue (Optional)
**Description**: Real-time port waiting queue information

| Column Name       | Data Type | Description                          |
|-------------------|-----------|--------------------------------------|
| Port_Name         | string    | Port name                            |
| Waiting_Vessels   | int       | Number of vessels waiting            |
| Avg_Wait_Hours    | float     | Average waiting time in hours        |
| Timestamp         | datetime  | Status timestamp                     |

---

## Silver Layer - Processed Data

### 1. Vessel_Processed
**Description**: Cleaned and validated vessel data with calculated fields

| Column Name           | Data Type | Description                              |
|-----------------------|-----------|------------------------------------------|
| Vessel_ID             | string    | Unique vessel identifier                 |
| Vessel_Type           | string    | LNG/LPG (filtered)                      |
| Latitude              | float     | Validated latitude                       |
| Longitude             | float     | Validated longitude                      |
| Speed_knots           | float     | Current speed (validated)                |
| Speed_30min_avg       | float     | 30-minute rolling average speed          |
| Speed_Volatility      | float     | Speed standard deviation (last 30 min)   |
| Heading               | float     | Vessel heading                           |
| Timestamp_UTC         | datetime  | Standardized UTC timestamp               |
| Destination_Port      | string    | Destination port                         |
| Distance_to_Dest_km   | float     | Calculated distance to destination       |
| Distance_to_Dest_nm   | float     | Distance in nautical miles               |
| Is_Moving             | boolean   | Speed > 1 knot                          |

**Processing Logic**:
- Remove invalid coordinates (lat/lon out of range)
- Filter only LNG/LPG vessels
- Calculate Haversine distance to destination dock
- Compute rolling statistics for speed
- Convert units (km ↔ nautical miles)

---

### 2. Dock_Status
**Description**: Real-time dock occupancy and availability

| Column Name       | Data Type | Description                          |
|-------------------|-----------|--------------------------------------|
| Dock_ID           | string    | Dock identifier                      |
| Port_Name         | string    | Port name                            |
| Latitude          | float     | Dock location                        |
| Longitude         | float     | Dock location                        |
| Berth_Count       | int       | Total berths                         |
| Occupied_Berth    | int       | Currently occupied berths            |
| Available_Berth   | int       | Available berths                     |
| Occupancy_Rate    | float     | Occupied / Total (0-1)              |
| Timestamp         | datetime  | Status update time                   |

---

## Gold Layer - Business Ready Data

### 1. ETA_Table
**Description**: Estimated Time of Arrival with risk scoring

| Column Name           | Data Type | Description                              |
|-----------------------|-----------|------------------------------------------|
| Vessel_ID             | string    | Vessel identifier                        |
| Vessel_Name           | string    | Vessel name                              |
| Vessel_Type           | string    | LNG/LPG                                 |
| Current_Latitude      | float     | Current position                         |
| Current_Longitude     | float     | Current position                         |
| Destination_Port      | string    | Target port                              |
| Destination_Dock_ID   | string    | Target dock                              |
| Distance_km           | float     | Distance to destination                  |
| Distance_nm           | float     | Distance in nautical miles               |
| Speed_knots           | float     | Current speed                            |
| Speed_30min_avg       | float     | Average speed (30 min)                  |
| Calculated_ETA_Hours  | float     | ETA in hours                            |
| Calculated_ETA_DateTime | datetime | Expected arrival date/time             |
| Speed_Volatility      | float     | Speed variation indicator                |
| Delay_Risk_Score      | float     | Risk score (0-100)                      |
| Risk_Category         | string    | Low/Medium/High                         |
| Last_Updated          | datetime  | Calculation timestamp                    |

**Calculation Formula**:
```
ETA (hours) = Distance (nautical miles) / Speed_30min_avg (knots)
Calculated_ETA_DateTime = Current_Time + ETA_Hours
```

**Risk Score Calculation**:
```
Delay_Risk_Score = (Speed_Volatility * 0.4) + (Congestion_Index * 0.4) + (Weather_Factor * 0.2)
```

---

### 2. Congestion_Index_Table
**Description**: Port congestion metrics

| Column Name           | Data Type | Description                              |
|-----------------------|-----------|------------------------------------------|
| Port_Name             | string    | Port name                                |
| Country               | string    | Country code                             |
| Total_Berths          | int       | Total available berths                   |
| Occupied_Berths       | int       | Currently occupied                       |
| Waiting_Vessels       | int       | Vessels in queue                         |
| Congestion_Index      | float     | Waiting vessels / Available berths       |
| Congestion_Level      | string    | Normal/Moderate/High/Critical           |
| Avg_Wait_Hours        | float     | Average waiting time                     |
| Vessels_24h_Incoming  | int       | Expected arrivals in 24 hours           |
| Timestamp             | datetime  | Status timestamp                         |

**Congestion Index Formula**:
```
Congestion_Index = Waiting_Vessels / (Total_Berths - Occupied_Berths)

Levels:
- Normal: < 0.5
- Moderate: 0.5 - 1.0
- High: 1.0 - 2.0
- Critical: > 2.0
```

---

### 3. Vessel_Live_Snapshot
**Description**: Current status of all tracked vessels (for PowerBI live dashboard)

| Column Name           | Data Type | Description                              |
|-----------------------|-----------|------------------------------------------|
| Vessel_ID             | string    | Vessel identifier                        |
| Vessel_Name           | string    | Vessel name                              |
| Vessel_Type           | string    | LNG/LPG                                 |
| Latitude              | float     | Current latitude                         |
| Longitude             | float     | Current longitude                        |
| Speed_knots           | float     | Current speed                            |
| Heading               | float     | Heading                                  |
| Destination_Port      | string    | Destination                              |
| ETA_Hours             | float     | Hours to arrival                         |
| ETA_DateTime          | datetime  | Expected arrival time                    |
| Distance_km           | float     | Remaining distance                       |
| Risk_Score            | float     | Delay risk score                         |
| Status                | string    | Underway/Moored/Anchored                |
| Last_Updated          | datetime  | Last position update                     |

---

## Data Quality Rules

### Validation Rules
- **Latitude**: -90 to 90
- **Longitude**: -180 to 180
- **Speed_knots**: 0 to 30 (reasonable range for cargo vessels)
- **Heading**: 0 to 360
- **Timestamp**: Must be within last 24 hours for real-time data

### Data Cleansing
- Remove duplicate records (same vessel, timestamp)
- Interpolate missing speed values using previous records
- Flag outliers in speed/position
- Standardize port names using master reference

### Data Lineage
- Bronze → Silver: Validation, filtering, distance calculation
- Silver → Gold: ETA calculation, risk scoring, aggregation

---

## File Naming Conventions

### Bronze Layer
```
AIS_Vessel_Raw_YYYYMMDD_HHMMSS.csv
Dock_Master_YYYYMMDD.csv
Port_Queue_YYYYMMDD_HHMMSS.csv
```

### Silver Layer
```
Vessel_Processed_YYYYMMDD.parquet
Dock_Status_YYYYMMDD.parquet
```

### Gold Layer
```
ETA_Table_YYYYMMDD.csv
Congestion_Index_YYYYMMDD.csv
Vessel_Live_Snapshot_Latest.csv
```

---

## Data Retention Policy

| Layer  | Retention Period | Archival Strategy              |
|--------|------------------|--------------------------------|
| Bronze | 30 days          | Archive to cold storage (S3)  |
| Silver | 90 days          | Compressed parquet files      |
| Gold   | 1 year           | Database + quarterly backups  |

---

## Integration Points

### Upstream Systems
- AIS API providers (MarineTraffic, VesselFinder)
- Port authority databases
- Weather API (optional)

### Downstream Systems
- Power BI (DirectQuery / Import)
- Internal ERP/SCM systems
- Alert notification system

---

## Next Steps
1. Set up data ingestion pipeline (Bronze layer)
2. Implement ETL logic (Bronze → Silver → Gold)
3. Build Power BI data model
4. Create real-time dashboard
