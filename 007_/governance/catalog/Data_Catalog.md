# Data Catalog

## Overview
This catalog provides metadata and definitions for all datasets in the Global Supply Chain Bottleneck & ETA Analysis System.

---

## Bronze Layer Datasets

### AIS_Vessel_Raw
**Description**: Real-time vessel position data from Automatic Identification System (AIS)

**Source**: AIS API (MarineTraffic / VesselFinder)
**Update Frequency**: Every 15-30 minutes
**Data Owner**: Data Engineering Team
**Sensitivity**: Public domain (AIS data)

**Business Purpose**: Track vessel movements for supply chain visibility

**Quality Metrics**:
- Completeness: > 95%
- Timeliness: < 30 minutes lag
- Accuracy: Validated against GPS standards

---

### Dock_Master
**Description**: Reference data for LNG/LPG terminal and docking facilities

**Source**: Port authorities, manual curation
**Update Frequency**: Monthly or as needed
**Data Owner**: Operations Team
**Sensitivity**: Internal use only

**Business Purpose**: Map vessels to destination facilities

**Quality Metrics**:
- Accuracy: 100% (manually verified)
- Currency: Updated within 30 days of changes

---

## Silver Layer Datasets

### Vessel_Processed
**Description**: Validated and enriched vessel data with calculated distances

**Source**: Transformed from AIS_Vessel_Raw
**Update Frequency**: Every 15-30 minutes
**Data Owner**: Data Analytics Team
**Sensitivity**: Internal use only

**Business Purpose**: Provide clean data for ETA calculations

**Transformations Applied**:
- Coordinate validation
- Speed validation
- Distance calculations (Haversine)
- Rolling speed statistics

---

## Gold Layer Datasets

### ETA_Table
**Description**: Business-ready ETA calculations with risk scores

**Source**: Calculated from Vessel_Processed
**Update Frequency**: Every 15-30 minutes
**Data Owner**: Data Analytics Team
**Sensitivity**: Confidential - Business critical

**Business Purpose**: Support operational decision-making

**Key Business Rules**:
- ETA calculated using 30-minute average speed
- Risk score weighted: 40% speed volatility, 40% congestion, 20% weather

**Consumers**:
- Trading teams
- Terminal operators
- Management dashboards

---

### Congestion_Index_Table
**Description**: Port congestion metrics and bottleneck indicators

**Source**: Aggregated from Vessel_Processed and Dock_Master
**Update Frequency**: Every 30 minutes
**Data Owner**: Operations Team
**Sensitivity**: Confidential

**Business Purpose**: Identify supply chain bottlenecks

**Alert Thresholds**:
- Normal: < 0.5
- Moderate: 0.5-1.0
- High: 1.0-2.0
- Critical: > 2.0

---

## Data Dictionary

### Common Fields

| Field Name    | Data Type | Description                | Valid Values       |
|---------------|-----------|----------------------------|--------------------|
| Vessel_ID     | string    | Unique vessel identifier   | MMSI number        |
| Vessel_Type   | string    | Type of vessel             | LNG, LPG           |
| Latitude      | float     | Geographic latitude        | -90 to 90          |
| Longitude     | float     | Geographic longitude       | -180 to 180        |
| Speed_knots   | float     | Vessel speed               | 0 to 30 knots      |
| Timestamp_UTC | datetime  | Record timestamp (UTC)     | ISO 8601 format    |

---

## Data Lineage

```
AIS API → AIS_Vessel_Raw (Bronze)
           ↓
    Validation & Enrichment
           ↓
    Vessel_Processed (Silver)
           ↓
    ETA Calculation & Risk Scoring
           ↓
    ETA_Table + Congestion_Index (Gold)
           ↓
    Power BI Dashboard
```

---

## Access Control

| Dataset              | Tier  | Access Level              |
|----------------------|-------|---------------------------|
| AIS_Vessel_Raw       | Bronze| Data Engineers            |
| Vessel_Processed     | Silver| Analytics Team            |
| ETA_Table            | Gold  | All internal users        |
| Congestion_Index     | Gold  | Operations & Management   |

---

**Last Updated**: 2026-01-23
**Maintained By**: Data Governance Team
