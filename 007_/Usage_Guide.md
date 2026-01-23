# Global Supply Chain Bottleneck & ETA Analysis System - Usage Guide

## 🎯 Project Overview

### Purpose
Real-time vessel tracking and ETA (Estimated Time of Arrival) calculation system to detect supply chain bottlenecks and optimize maritime logistics.

### Key Features
- Real-time vessel position tracking (AIS-based)
- Automated ETA calculation
- Port congestion monitoring
- Delay risk assessment
- Interactive Power BI dashboards

### Target Users
- LNG/LPG Trading Companies
- Terminal Operators
- Energy Companies
- Shipping Companies
- Supply Chain Operations Teams

---

## 📁 Project Structure

```
007_Global_SupplyChain_Bottleneck_ETA/
│
├─ data/
│  ├─ bronze/          # Raw AIS data, dock master data
│  ├─ silver/          # Processed & validated data
│  └─ gold/            # Business-ready analytics tables
│
├─ governance/
│  ├─ catalog/         # Data dictionary & metadata
│  ├─ lineage/         # ETL process documentation
│  ├─ quality/         # Data quality rules & reports
│  └─ policy/          # Access control & compliance
│
├─ notebooks/
│  ├─ 01_data_ingestion_bronze.py      # AIS data collection
│  ├─ 02_data_processing_silver.py     # Data cleaning & validation
│  └─ 03_eta_calculation_gold.py       # ETA & risk calculation
│
├─ powerbi/
│  ├─ dashboards/      # Power BI dashboard files (.pbix)
│  └─ datasets/        # Data models for Power BI
│
├─ docs/
│  ├─ private/         # Technical documentation
│  │  ├─ Data_Schema.md                # Complete data schema
│  │  └─ PowerBI_Dashboard_Guide.md    # Dashboard implementation
│  ├─ public/          # External stakeholder documents
│  ├─ appendix/        # Additional resources
│  └─ Image/           # Dashboard screenshots, diagrams
│
├─ Release.md          # Version history & changelog
└─ Usage_Guide.md      # This file
```

---

## 🚀 Getting Started

### Prerequisites

#### Python Environment
```bash
Python 3.8+
pandas
numpy
requests (for AIS API)
datetime
```

Install dependencies:
```bash
pip install pandas numpy requests
```

#### Power BI
- Power BI Desktop (latest version)
- Azure Maps Visual (install from AppSource)
- Power BI Pro/Premium license (for publishing)

#### Data Sources
- AIS API access (MarineTraffic, VesselFinder, or similar)
- Dock/Terminal master data
- (Optional) Weather API for enhanced risk scoring

---

## 📊 Data Pipeline Workflow

### Step 1: Data Ingestion (Bronze Layer)

**Notebook**: `notebooks/01_data_ingestion_bronze.py`

**Purpose**: Collect raw AIS vessel data and dock information

**Run**:
```bash
cd notebooks
python 01_data_ingestion_bronze.py
```

**Outputs**:
- `data/bronze/AIS_Vessel_Raw_YYYYMMDD_HHMMSS.csv`
- `data/bronze/Dock_Master_YYYYMMDD.csv`

**Frequency**: Every 15-30 minutes (real-time scenarios)

---

### Step 2: Data Processing (Silver Layer)

**Notebook**: `notebooks/02_data_processing_silver.py`

**Purpose**:
- Validate coordinates and speed
- Filter LNG/LPG vessels
- Calculate Haversine distance to destination
- Compute rolling speed statistics

**Run**:
```bash
python 02_data_processing_silver.py
```

**Key Functions**:
- `haversine_distance()`: Calculate distance between two geographic points
- `validate_coordinates()`: Remove invalid lat/lon data
- `calculate_distance_to_destination()`: Compute distance to dock

**Outputs**:
- `data/silver/Vessel_Processed_YYYYMMDD.csv`

---

### Step 3: ETA Calculation (Gold Layer)

**Notebook**: `notebooks/03_eta_calculation_gold.py`

**Purpose**:
- Calculate ETA using distance and speed
- Compute port congestion index
- Assign delay risk scores
- Generate business-ready tables

**Run**:
```bash
python 03_eta_calculation_gold.py
```

**Key Calculations**:

**ETA Formula**:
```python
ETA (hours) = Distance (nautical miles) / Speed_30min_avg (knots)
```

**Congestion Index**:
```python
Congestion_Index = Waiting_Vessels / Available_Berths
```

**Risk Score**:
```python
Risk_Score = (Speed_Volatility * 0.4) +
             (Congestion_Index * 0.4) +
             (Weather_Factor * 0.2)
```

**Outputs**:
- `data/gold/ETA_Table_YYYYMMDD.csv`
- `data/gold/Congestion_Index_YYYYMMDD.csv`
- `data/gold/Vessel_Live_Snapshot_Latest.csv`

---

## 📈 Power BI Dashboard

### Opening the Dashboard

1. Navigate to `powerbi/dashboards/`
2. Open the `.pbix` file in Power BI Desktop
3. Click **Refresh** to load latest data

### Dashboard Pages

#### Page 1: Global Overview
- **Azure Map**: Real-time vessel positions
- **Heatmap**: Port congestion visualization
- **Vessel markers**: Color-coded by type (LNG/LPG)
- **Dock markers**: Port locations with capacity info

#### Page 2: KPI Dashboard
- **KPI Cards**:
  - Average ETA
  - Vessels arriving within 24h
  - Average risk score
  - Number of critical ports

- **Charts**:
  - Top 10 congested ports (bar chart)
  - Risk distribution (donut chart)
  - ETA timeline (line chart)

- **Tables**:
  - High-risk vessels
  - Port status summary

#### Page 3: Vessel Details (Drill-through)
- Detailed vessel information
- Route visualization
- ETA calculation breakdown
- Historical speed chart

### Using Filters

**Slicers available**:
- Vessel Type (LNG / LPG)
- Risk Category (Low / Medium / High)
- Destination Port
- Country
- ETA Range

**Interaction**:
- Click on map markers for details
- Use slicers to filter all visuals
- Drill-through by right-clicking vessel in table

---

## 🔔 Alert Configuration

### Real-time Alerts

Configure alerts in Power BI Service for:

1. **High Congestion**
   - Trigger: Congestion Index > 2.0
   - Action: Email to operations team

2. **Critical ETA**
   - Trigger: High-risk vessel with ETA < 12 hours
   - Action: Notify port coordinator

3. **Capacity Warning**
   - Trigger: Available berths < 2
   - Action: Alert terminal manager

---

## 📊 Key Metrics & KPIs

### Primary KPIs

| KPI                    | Definition                                | Target            |
|------------------------|-------------------------------------------|-------------------|
| Average ETA            | Mean ETA for all vessels in transit       | < 72 hours        |
| 24h Arrival Count      | Vessels arriving within 24 hours          | Monitor capacity  |
| Average Risk Score     | Mean delay risk score                     | < 40              |
| Congestion Index       | Waiting vessels / Available berths        | < 1.0             |
| High-Risk Vessels      | Vessels with risk score > 60              | Minimize          |

### Risk Categories

- **Low Risk** (0-30): Normal operations, no delays expected
- **Medium Risk** (30-60): Minor delays possible, monitor closely
- **High Risk** (60-100): Significant delays likely, take action

### Congestion Levels

- **Normal** (< 0.5): No congestion
- **Moderate** (0.5-1.0): Some waiting expected
- **High** (1.0-2.0): Significant delays
- **Critical** (> 2.0): Severe congestion, urgent action needed

---

## 🎯 Business Use Cases

### Use Case 1: LNG Trading Company

**Scenario**: Monitor cargo vessels and adjust spot contracts based on arrival delays

**How to Use**:
1. Open dashboard and filter for LNG vessels
2. Check ETA for key shipments
3. Identify high-risk arrivals
4. Review congestion at destination ports
5. Adjust trading positions if delays detected

**Value**: Reduce exposure to price volatility, optimize inventory

---

### Use Case 2: Terminal Operator

**Scenario**: Optimize berth allocation and reduce waiting times

**How to Use**:
1. Monitor Port Status table
2. Review incoming vessels (24h view)
3. Check congestion index for each dock
4. Pre-allocate berths for arriving vessels
5. Coordinate with vessels experiencing delays

**Value**: Increase terminal efficiency, reduce demurrage costs

---

### Use Case 3: Shipping Company

**Scenario**: Minimize vessel waiting time and fuel costs

**How to Use**:
1. Track company vessels on map
2. Monitor ETA accuracy
3. Identify ports with high congestion
4. Adjust sailing speed to optimize arrival timing
5. Reroute if alternative ports available

**Value**: Reduce fuel costs, improve on-time performance

---

## 🔧 Customization

### Adding New Vessel Types

Edit `notebooks/02_data_processing_silver.py`:

```python
def filter_vessel_types(df, vessel_types=['LNG', 'LPG', 'AMMONIA']):
    # Add new vessel types to the list
```

### Adjusting Risk Score Weights

Edit `notebooks/03_eta_calculation_gold.py`:

```python
# Current weights
speed_risk = df['Speed_Volatility'] * 100 * 0.4
congestion_risk = df['Port_Congestion_Index'] * 20 * 0.4
weather_risk = np.random.uniform(0, 20, len(df)) * 0.2

# Adjust weights as needed (must sum to 1.0)
```

### Custom ETA Calculation

Modify the ETA formula to include additional factors:

```python
# Standard ETA
df['Calculated_ETA_Hours'] = df['Distance_to_Dest_nm'] / df['Speed_30min_avg']

# Custom: Add weather delay buffer
weather_delay_hours = 2  # Example: 2-hour buffer
df['Calculated_ETA_Hours'] = df['Calculated_ETA_Hours'] + weather_delay_hours
```

---

## 🔄 Automation & Scheduling

### Windows Task Scheduler

Create scheduled tasks for notebooks:

```bash
# Run every 30 minutes
Task Name: AIS_Data_Pipeline
Program: python.exe
Arguments: C:\path\to\notebooks\01_data_ingestion_bronze.py
Trigger: Daily, repeat every 30 minutes
```

### Linux Cron Job

```bash
# Add to crontab
*/30 * * * * cd /path/to/notebooks && python3 01_data_ingestion_bronze.py
*/30 * * * * cd /path/to/notebooks && python3 02_data_processing_silver.py
*/30 * * * * cd /path/to/notebooks && python3 03_eta_calculation_gold.py
```

### Power BI Scheduled Refresh

1. Publish dashboard to Power BI Service
2. Go to **Settings** → **Scheduled Refresh**
3. Set frequency: **Every 30 minutes** (requires Premium)
4. Configure gateway credentials

---

## 🐛 Troubleshooting

### Issue: No data in dashboard

**Possible Causes**:
- Data files not generated by notebooks
- Incorrect file paths in Power BI
- Data refresh not configured

**Solution**:
1. Run notebooks manually to generate data
2. Check `data/gold/` folder for CSV files
3. Update data source paths in Power BI
4. Click **Refresh** in Power BI

---

### Issue: ETA calculations seem incorrect

**Possible Causes**:
- Speed data missing or zero
- Distance calculation error
- Unit conversion issue

**Solution**:
1. Check `data/silver/Vessel_Processed_*.csv`
2. Verify `Speed_30min_avg` column has valid values
3. Confirm `Distance_to_Dest_nm` is in nautical miles
4. Review `haversine_distance()` function

---

### Issue: Map not displaying vessels

**Possible Causes**:
- Azure Maps visual not installed
- Latitude/Longitude data type issue
- Invalid coordinates

**Solution**:
1. Install Azure Maps visual from AppSource
2. Ensure lat/lon columns are **Decimal Number** type
3. Check data for invalid coordinates (e.g., null, out of range)

---

## 📚 Additional Resources

### Documentation
- **Data Schema**: `docs/private/Data_Schema.md`
- **Power BI Guide**: `docs/private/PowerBI_Dashboard_Guide.md`
- **Release Notes**: `Release.md`

### External Links
- AIS Data Providers: MarineTraffic, VesselFinder
- Haversine Formula: [Wikipedia](https://en.wikipedia.org/wiki/Haversine_formula)
- Power BI Documentation: [Microsoft Docs](https://docs.microsoft.com/power-bi/)

### Support
- Internal: Contact Data Analytics Team
- Issues: Document in `governance/quality/`

---

## 🎓 Training Resources

### For Business Users
1. **Dashboard Navigation** (30 min)
   - Understanding KPIs
   - Using filters and slicers
   - Interpreting risk scores

2. **Scenario Analysis** (45 min)
   - Identifying bottlenecks
   - Making operational decisions
   - Exporting data for reports

### For Technical Users
1. **Data Pipeline Overview** (1 hour)
   - Bronze → Silver → Gold layers
   - Python notebook structure
   - Scheduling & automation

2. **Advanced Customization** (2 hours)
   - Modifying calculations
   - Adding data sources
   - Creating custom visuals

---

## ⚠️ Important Notes

### Data Accuracy
- AIS data may have delays (5-15 minutes typical)
- ETA calculations are estimates, not guarantees
- Weather and port conditions can affect actual arrival times

### Data Privacy
- AIS data is generally public domain
- Respect data usage agreements with API providers
- Internal operational data should be protected

### Performance
- Large datasets (>10,000 vessels) may impact dashboard performance
- Consider filtering to relevant regions/vessel types
- Use DirectQuery for very large datasets

---

## 🔮 Future Enhancements

### Planned Features
- [ ] Weather API integration for enhanced risk scoring
- [ ] Machine Learning ETA prediction model
- [ ] Automated email alerts
- [ ] Mobile app for on-the-go monitoring
- [ ] Integration with ERP/SCM systems
- [ ] Historical trend analysis
- [ ] Carbon emissions tracking

### Roadmap
- **Q1 2026**: ML-based ETA prediction
- **Q2 2026**: Weather integration
- **Q3 2026**: Mobile app launch
- **Q4 2026**: API for external systems

---

## 📞 Contact & Support

**Project Owner**: Data Analytics Team
**Email**: analytics@company.com
**Slack**: #supply-chain-analytics
**Documentation**: SharePoint/Confluence link

---

**Last Updated**: 2026-01-23
**Version**: 1.0.0
**Author**: Data Analysis Team
