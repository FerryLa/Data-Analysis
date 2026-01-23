# Power BI Dashboard Implementation Guide

## Overview
This guide provides step-by-step instructions for building the Global Supply Chain Bottleneck & ETA Analysis Dashboard in Power BI.

---

## Dashboard Architecture

### Data Model Structure
```
ETA_Table (Fact)
├─ Vessel_ID (Key)
├─ Calculated_ETA_Hours
├─ Delay_Risk_Score
└─ Risk_Category

Congestion_Index_Table (Fact)
├─ Port_Name (Key)
├─ Congestion_Index
└─ Congestion_Level

Vessel_Live_Snapshot (Fact)
├─ Vessel_ID (Key)
├─ Latitude, Longitude
├─ ETA_DateTime
└─ Risk_Score

Dock_Master (Dimension)
├─ Dock_ID (Key)
├─ Port_Name
└─ Country
```

---

## Step 1: Data Connection

### Import Gold Layer Data

1. Open Power BI Desktop
2. Click **Get Data** → **Text/CSV**
3. Import the following files from `data/gold/`:
   - `ETA_Table_YYYYMMDD.csv`
   - `Congestion_Index_YYYYMMDD.csv`
   - `Vessel_Live_Snapshot_Latest.csv`

4. Import from `data/bronze/`:
   - `Dock_Master_YYYYMMDD.csv`

### Data Refresh Settings

For **real-time** updates:
- Set up **DirectQuery** or **Live Connection** if using SQL database
- Configure **Scheduled Refresh** (every 15-30 minutes)
- Use Power BI Service with Gateway for automated refresh

---

## Step 2: Data Model Relationships

### Create Relationships

1. **ETA_Table** → **Dock_Master**
   - `Destination_Port` (ETA_Table) → `Port_Name` (Dock_Master)
   - Cardinality: Many to One

2. **Congestion_Index_Table** → **Dock_Master**
   - `Port_Name` (Congestion_Index) → `Port_Name` (Dock_Master)
   - Cardinality: One to One

3. **Vessel_Live_Snapshot** → **ETA_Table**
   - `Vessel_ID` (Snapshot) → `Vessel_ID` (ETA_Table)
   - Cardinality: One to One

---

## Step 3: DAX Measures

### Create these measures in Power BI:

#### KPI Measures

```dax
// Average ETA (Hours)
Avg_ETA_Hours =
AVERAGE(ETA_Table[Calculated_ETA_Hours])

// Vessels Arriving Within 24h
Vessels_24h =
CALCULATE(
    COUNTROWS(ETA_Table),
    ETA_Table[Calculated_ETA_Hours] <= 24
)

// Average Risk Score
Avg_Risk_Score =
AVERAGE(ETA_Table[Delay_Risk_Score])

// High Risk Vessel Count
High_Risk_Vessels =
CALCULATE(
    COUNTROWS(ETA_Table),
    ETA_Table[Risk_Category] = "High"
)

// Total Vessels Tracked
Total_Vessels =
COUNTROWS(Vessel_Live_Snapshot)
```

#### Congestion Measures

```dax
// Average Congestion Index
Avg_Congestion =
AVERAGE(Congestion_Index_Table[Congestion_Index])

// Critical Ports Count
Critical_Ports =
CALCULATE(
    COUNTROWS(Congestion_Index_Table),
    Congestion_Index_Table[Congestion_Level] = "Critical"
)

// Total Incoming Vessels (24h)
Total_Incoming_24h =
SUM(Congestion_Index_Table[Vessels_24h_Incoming])
```

#### Time Intelligence Measures

```dax
// ETA Days Remaining
ETA_Days_Remaining =
DIVIDE(
    ETA_Table[Calculated_ETA_Hours],
    24,
    0
)

// Hours to Next Arrival
Hours_to_Next_Arrival =
MINX(
    ETA_Table,
    ETA_Table[Calculated_ETA_Hours]
)
```

---

## Step 4: Dashboard Design

### Page 1: Global Overview Map

#### Azure Maps Visual

1. Install **Azure Maps** visual from AppSource
2. Configure settings:
   - **Location**: `Vessel_Live_Snapshot[Latitude]`, `Vessel_Live_Snapshot[Longitude]`
   - **Size**: `Vessel_Live_Snapshot[Risk_Score]`
   - **Color**: `Vessel_Live_Snapshot[Vessel_Type]`
     - LNG → Blue (#0078D4)
     - LPG → Orange (#FF8C00)

3. Add **Dock locations**:
   - Location: `Dock_Master[Latitude]`, `Dock_Master[Longitude]`
   - Icon: Black marker
   - Tooltip: Port name, berth count

4. Add **Heatmap Layer**:
   - Data: `Congestion_Index_Table[Port_Name]`
   - Intensity: `Congestion_Index_Table[Congestion_Index]`
   - Color gradient: Green → Yellow → Red

#### Map Settings
```
Zoom Level: Auto-fit
Base Map: Road
Show Labels: Yes
Enable Clustering: No (for precise vessel positions)
```

---

### Page 2: KPI Dashboard

#### Top Row - KPI Cards

Create 4 KPI cards:

1. **Average ETA**
   - Measure: `Avg_ETA_Hours`
   - Format: `0.0 "hours"`
   - Trend: Compare to previous refresh

2. **Vessels Arriving 24h**
   - Measure: `Vessels_24h`
   - Icon: Ship
   - Color: Blue

3. **Average Risk Score**
   - Measure: `Avg_Risk_Score`
   - Format: `0.0`
   - Conditional formatting:
     - < 30: Green
     - 30-60: Yellow
     - > 60: Red

4. **Critical Ports**
   - Measure: `Critical_Ports`
   - Icon: Warning
   - Color: Red if > 0

---

#### Middle Section - Charts

1. **Top 10 Congested Ports (Bar Chart)**
   - Axis: `Congestion_Index_Table[Port_Name]`
   - Values: `Congestion_Index_Table[Congestion_Index]`
   - Sort: Descending
   - Color by: `Congestion_Level`

2. **Risk Distribution (Donut Chart)**
   - Legend: `ETA_Table[Risk_Category]`
   - Values: Count of vessels
   - Colors:
     - Low: Green
     - Medium: Yellow
     - High: Red

3. **ETA Timeline (Line Chart)**
   - X-axis: `ETA_Table[Calculated_ETA_DateTime]`
   - Y-axis: Count of vessels
   - Group by hour/day

---

#### Bottom Section - Data Tables

1. **High Risk Vessels Table**
   - Filter: `Risk_Category = "High"`
   - Columns:
     - Vessel Name
     - Destination Port
     - ETA Hours
     - Risk Score
   - Sort by: Risk Score (descending)

2. **Port Status Table**
   - Columns:
     - Port Name
     - Congestion Level
     - Incoming Vessels (24h)
     - Available Berths
   - Conditional formatting on Congestion Level

---

### Page 3: Vessel Details (Drill-through)

Create a drill-through page with:

1. **Vessel Information Card**
   - Vessel ID, Name, Type
   - Current Speed, Heading
   - Last Updated timestamp

2. **Route Map**
   - Current position → Destination
   - Show great circle route (optional)

3. **ETA Calculation Details**
   - Distance remaining (km & nm)
   - Current speed
   - Average speed (30 min)
   - Calculated ETA
   - Risk factors breakdown

4. **Historical Speed Chart**
   - X-axis: Time
   - Y-axis: Speed (knots)
   - Show volatility

---

## Step 5: Interactivity

### Slicers

Add the following slicers to enable filtering:

1. **Vessel Type** (LNG / LPG)
2. **Risk Category** (Low / Medium / High)
3. **Destination Port** (multi-select dropdown)
4. **Country** (from Dock_Master)
5. **ETA Range** (< 6h, 6-12h, 12-24h, > 24h)

### Cross-filtering

Enable cross-filtering between:
- Map → KPIs
- Risk chart → Vessel table
- Port congestion → Map

---

## Step 6: Tooltips

### Custom Tooltip for Map Markers

Create a tooltip page with:
- Vessel Name
- Current Speed
- Destination
- ETA (hours & datetime)
- Risk Score with color indicator

### Port Tooltip

- Port Name
- Congestion Level
- Available Berths
- Incoming Vessels (24h)
- Average Wait Time

---

## Step 7: Alerts & Notifications

### Configure Data Alerts

Set up alerts for:

1. **Critical Congestion**
   - Condition: `Congestion_Index > 2.0`
   - Action: Email stakeholders

2. **High Risk Arrivals**
   - Condition: `Risk_Score > 80 AND ETA_Hours < 12`
   - Action: Send alert

3. **Berth Capacity**
   - Condition: `Available_Berths < 2`
   - Action: Notify port operations

---

## Step 8: Publishing & Sharing

### Publish to Power BI Service

1. Click **Publish** in Power BI Desktop
2. Select workspace
3. Configure **scheduled refresh**:
   - Frequency: Every 30 minutes
   - Time zone: UTC
   - Credentials: Configure gateway

### Create App

1. In Power BI Service, create a new App
2. Add dashboard to App
3. Set permissions:
   - **Operations Team**: Full access
   - **Management**: View only
   - **External Partners**: Specific reports only

### Embed Options

- **Web Portal**: Use embed code
- **Teams**: Add Power BI tab
- **Mobile**: Enable mobile layout

---

## Step 9: Performance Optimization

### Optimize for Real-time

1. **Use DirectQuery** for live data
2. **Reduce visual complexity** on main page
3. **Implement incremental refresh**:
   - Archive data older than 30 days
   - Keep only recent data in-memory

4. **Optimize DAX**:
   - Use variables to avoid recalculation
   - Filter early in measures
   - Avoid complex calculated columns

### Example Optimized DAX

```dax
// Optimized ETA calculation
ETA_Optimized =
VAR _CurrentTime = NOW()
VAR _FilteredVessels =
    FILTER(
        ETA_Table,
        ETA_Table[Calculated_ETA_Hours] < 48
    )
RETURN
    AVERAGEX(_FilteredVessels, [Calculated_ETA_Hours])
```

---

## Step 10: Mobile Layout

### Design Mobile View

1. Switch to **Mobile Layout** in Power BI Desktop
2. Prioritize:
   - KPI cards at top
   - Simplified map
   - Top 5 congested ports
   - High risk vessel list

3. Optimize for touch:
   - Larger buttons
   - Simple navigation
   - Essential info only

---

## Color Scheme

### Standard Colors

| Element           | Color Code | Usage                    |
|-------------------|------------|--------------------------|
| LNG Vessels       | #0078D4    | Blue - primary           |
| LPG Vessels       | #FF8C00    | Orange - secondary       |
| Low Risk          | #107C10    | Green                    |
| Medium Risk       | #FFB900    | Yellow                   |
| High Risk         | #D13438    | Red                      |
| Docks             | #000000    | Black                    |
| Background        | #F3F2F1    | Light gray               |

---

## Sample Layout Screenshots

### Dashboard Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│  GLOBAL SUPPLY CHAIN BOTTLENECK & ETA DASHBOARD        │
├─────────────────────────────────────────────────────────┤
│  [Avg ETA] [Vessels 24h] [Risk Score] [Critical Ports] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                  AZURE MAP - GLOBAL VIEW                │
│              (Vessels + Ports + Heatmap)                │
│                                                         │
├──────────────────────────┬──────────────────────────────┤
│  Top Congested Ports     │    Risk Distribution         │
│  (Bar Chart)             │    (Donut Chart)             │
├──────────────────────────┴──────────────────────────────┤
│              High Risk Vessels Table                    │
└─────────────────────────────────────────────────────────┘
```

---

## Testing Checklist

- [ ] All data sources connected
- [ ] Relationships configured correctly
- [ ] DAX measures calculate properly
- [ ] Map displays vessels and ports
- [ ] Heatmap shows congestion
- [ ] KPI cards update with filters
- [ ] Drill-through works
- [ ] Tooltips display correctly
- [ ] Scheduled refresh configured
- [ ] Mobile layout functional
- [ ] Performance acceptable (< 3s load time)
- [ ] Alerts configured and tested

---

## Troubleshooting

### Common Issues

**Issue**: Map not displaying vessels
- **Solution**: Check latitude/longitude data types (must be decimal)
- Verify Azure Maps visual is installed

**Issue**: Slow performance
- **Solution**: Use DirectQuery, implement aggregations
- Reduce number of visuals per page

**Issue**: Data not refreshing
- **Solution**: Check gateway connection
- Verify file paths in data source settings

**Issue**: Relationships not working
- **Solution**: Check data types match
- Ensure cardinality is set correctly

---

## Next Steps

1. Deploy to production Power BI workspace
2. Train end users on dashboard navigation
3. Set up monitoring for data refresh failures
4. Gather feedback and iterate
5. Plan for advanced features (weather integration, ML predictions)

---

## Resources

- Power BI Documentation: https://docs.microsoft.com/power-bi/
- DAX Reference: https://dax.guide/
- Azure Maps Visual: https://azuremaps.com/
- Community Forum: https://community.powerbi.com/

---

**Last Updated**: 2026-01-23
**Author**: Data Analysis Team
