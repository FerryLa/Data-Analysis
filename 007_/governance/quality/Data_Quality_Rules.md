# Data Quality Rules

## Overview
This document defines data quality standards, validation rules, and monitoring procedures for the Global Supply Chain Bottleneck & ETA Analysis System.

---

## Quality Dimensions

### 1. Accuracy
Data correctly represents real-world values

### 2. Completeness
All required fields are populated

### 3. Consistency
Data is consistent across sources and over time

### 4. Timeliness
Data is available when needed

### 5. Validity
Data conforms to defined formats and ranges

### 6. Uniqueness
No duplicate records exist

---

## Validation Rules

### Bronze Layer - AIS_Vessel_Raw

#### Rule 1: Coordinate Range Validation
```
Status: MANDATORY
Field: Latitude, Longitude
Rule:
  - Latitude must be between -90 and 90
  - Longitude must be between -180 and 180
Action on Failure: Reject record
```

#### Rule 2: Speed Validation
```
Status: MANDATORY
Field: Speed_knots
Rule: Speed must be between 0 and 30 knots
Rationale: Cargo vessels typically don't exceed 25 knots
Action on Failure: Flag for review
```

#### Rule 3: Timestamp Recency
```
Status: CRITICAL
Field: Timestamp
Rule: Timestamp must be within last 24 hours
Rationale: Real-time system requires recent data
Action on Failure: Reject record
```

#### Rule 4: Vessel ID Format
```
Status: MANDATORY
Field: Vessel_ID
Rule: Must be valid MMSI number (9 digits)
Action on Failure: Reject record
```

#### Rule 5: Completeness Check
```
Status: MANDATORY
Fields: Vessel_ID, Latitude, Longitude, Speed_knots, Timestamp
Rule: All critical fields must be non-null
Action on Failure: Reject record
```

---

### Silver Layer - Vessel_Processed

#### Rule 6: Distance Calculation Verification
```
Status: WARNING
Field: Distance_to_Dest_km
Rule: Distance should be > 0 and < 40,000 km (Earth circumference)
Action on Failure: Flag for review
```

#### Rule 7: Speed Statistics Validation
```
Status: MANDATORY
Field: Speed_30min_avg
Rule: Must be within ±20% of current speed
Rationale: Average shouldn't deviate drastically
Action on Failure: Recalculate or flag
```

#### Rule 8: Vessel Type Filter
```
Status: MANDATORY
Field: Vessel_Type
Rule: Must be 'LNG' or 'LPG'
Action on Failure: Exclude from analysis
```

---

### Gold Layer - ETA_Table

#### Rule 9: ETA Reasonableness
```
Status: CRITICAL
Field: Calculated_ETA_Hours
Rule:
  - ETA must be > 0
  - ETA should be < 720 hours (30 days)
Rationale: Unrealistic ETAs indicate data issues
Action on Failure: Flag for review, exclude from KPIs
```

#### Rule 10: Risk Score Range
```
Status: MANDATORY
Field: Delay_Risk_Score
Rule: Risk score must be between 0 and 100
Action on Failure: Recalculate
```

#### Rule 11: Risk Category Consistency
```
Status: MANDATORY
Fields: Delay_Risk_Score, Risk_Category
Rule:
  - Low: 0-30
  - Medium: 30-60
  - High: 60-100
Action on Failure: Correct category assignment
```

---

### Gold Layer - Congestion_Index_Table

#### Rule 12: Congestion Index Validity
```
Status: MANDATORY
Field: Congestion_Index
Rule: Must be >= 0
Rationale: Cannot have negative congestion
Action on Failure: Investigate calculation logic
```

#### Rule 13: Berth Count Validation
```
Status: MANDATORY
Fields: Total_Berths, Occupied_Berths
Rule:
  - Both must be >= 0
  - Occupied_Berths <= Total_Berths
Action on Failure: Flag data source issue
```

---

## Quality Monitoring

### Automated Checks

**Frequency**: Every data refresh (15-30 minutes)

**Checks Performed**:
1. Record count validation (expect > 0 records)
2. Null value percentage (< 5% for critical fields)
3. Duplicate detection
4. Outlier detection (statistical)

**Alerting**:
- Email notification if critical rules fail
- Dashboard indicator for warning-level failures

---

### Quality Metrics

#### Bronze Layer Metrics

| Metric                     | Target  | Measured      |
|----------------------------|---------|---------------|
| Completeness (critical)    | > 95%   | Daily         |
| Timeliness (data lag)      | < 30min | Per refresh   |
| Duplicate rate             | < 1%    | Daily         |
| Coordinate validity        | 100%    | Per refresh   |

#### Silver Layer Metrics

| Metric                     | Target  | Measured      |
|----------------------------|---------|---------------|
| Processing success rate    | > 99%   | Per refresh   |
| Distance calc accuracy     | 100%    | Spot check    |
| Speed outliers             | < 2%    | Daily         |

#### Gold Layer Metrics

| Metric                     | Target  | Measured      |
|----------------------------|---------|---------------|
| ETA calculation success    | > 99%   | Per refresh   |
| Risk score distribution    | Stable  | Weekly        |
| Congestion accuracy        | > 95%   | Manual verify |

---

## Data Cleansing Procedures

### Handling Missing Values

**Speed_knots missing**:
- Action: Interpolate from previous/next records
- If unavailable: Exclude from ETA calculation

**Destination_Port missing**:
- Action: Attempt to infer from vessel route
- If unavailable: Mark as "Unknown", exclude from analysis

**Coordinates missing**:
- Action: Cannot process, reject record

---

### Handling Outliers

**Abnormal Speed (> 30 knots)**:
- Action: Flag for review, cap at 30 knots if clearly erroneous

**ETA > 30 days**:
- Action: Investigate distance/speed calculation
- Possible vessel stopped or data error

**Negative Distance**:
- Action: Critical error - investigate Haversine calculation

---

### Deduplication

**Duplicate Detection**:
- Key: Vessel_ID + Timestamp (rounded to nearest minute)
- Action: Keep most recent record, remove duplicates

---

## Quality Reports

### Daily Quality Report

**Contents**:
- Total records processed
- Validation failures by rule
- Data quality score (weighted average)
- Trending charts

**Distribution**: Data Engineering, Analytics Team

---

### Weekly Quality Summary

**Contents**:
- Quality metrics vs targets
- Top data quality issues
- Remediation actions taken
- Improvement recommendations

**Distribution**: Management, Operations Team

---

## Quality Improvement Process

### Issue Escalation

**Severity Levels**:

1. **Critical**: Data pipeline stopped, no ETA calculations
   - Response: Immediate (< 1 hour)
   - Owner: Data Engineering

2. **High**: Significant data loss (> 20% records rejected)
   - Response: Same day
   - Owner: Data Engineering + Analytics

3. **Medium**: Quality degradation (metrics below target)
   - Response: Within 3 days
   - Owner: Analytics Team

4. **Low**: Minor issues, no impact on KPIs
   - Response: Next sprint
   - Owner: Analytics Team

---

### Root Cause Analysis

**Trigger**: Any high or critical severity issue

**Process**:
1. Identify failure point (Bronze/Silver/Gold layer)
2. Review logs and error messages
3. Analyze data samples
4. Determine root cause (source data, logic error, infrastructure)
5. Document findings
6. Implement fix
7. Validate fix
8. Update quality rules if needed

---

## Data Quality Dashboard

### KPIs to Monitor

1. **Overall Data Quality Score** (0-100)
   - Weighted average of all quality dimensions
   - Target: > 90

2. **Record Success Rate**
   - (Valid records / Total records) * 100
   - Target: > 95%

3. **Validation Failure Rate**
   - Records failing validation / Total records
   - Target: < 5%

4. **Data Freshness**
   - Time since last successful refresh
   - Target: < 30 minutes

---

## Governance

### Data Quality Ownership

| Layer  | Owner                  | Responsibilities                 |
|--------|------------------------|----------------------------------|
| Bronze | Data Engineering Team  | Source data validation           |
| Silver | Analytics Team         | Transformation quality           |
| Gold   | Analytics + Operations | Business logic accuracy          |

### Review Cycle

- **Monthly**: Review quality rules, update thresholds
- **Quarterly**: Assess quality metrics trends, improvement initiatives
- **Annually**: Comprehensive quality audit

---

## References

- Data Schema: `docs/private/Data_Schema.md`
- Data Catalog: `governance/catalog/Data_Catalog.md`
- Incident Response: `governance/policy/Incident_Response.md` (TBD)

---

**Last Updated**: 2026-01-23
**Maintained By**: Data Quality Team
**Review Date**: 2026-02-23
