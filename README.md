# MySQL InnoDB Primary Key Study  
## Auto-Increment vs Random Primary Keys Under Long-Running Workloads

This repository contains a **long-running empirical study** of MySQL InnoDB behavior comparing:

- **AUTO_INCREMENT primary keys**
- **Random BIGINT primary keys**

The focus is not short-lived benchmarks, but **how InnoDB behaves over time**, especially after a table exits the growth phase and enters a **steady-state insert/delete workload**.

---

## Why This Study Exists

Most MySQL guidance recommends using `AUTO_INCREMENT` primary keys because:

- Inserts are append-only
- Page splits are minimized
- Insert performance is excellent during growth

However, real production systems often:
- Run continuously for months or years
- Perform frequent inserts *and* deletes
- Stabilize in total row count
- Care about **predictability, disk usage, and background maintenance cost**

This study explores what happens **after the initial growth phase**, when the system starts churning data rather than growing indefinitely.

---

## High-Level Experiment Design

Two identical InnoDB tables are used:

| Table Name | Primary Key Type |
|-----------|------------------|
| `seq_pk7` | `BIGINT AUTO_INCREMENT` |
| `uuid_pk7` | Random `BIGINT` |

Both tables:
- Use the same schema
- Store identical payload sizes
- Receive identical workloads

---

## Workload Characteristics

Each iteration performs:

1. Batch inserts
2. Batch deletes
3. Metric collection

This loop runs continuously to allow the system to:
- Grow initially
- Reach steady-state
- Exhibit long-term structural behavior

Deletes are intentional and essential — without deletes, steady-state behavior cannot be observed.

---

## Metrics Collected

Metrics are collected directly from MySQL and written to CSV for offline analysis.

### 1. Data Size
- Table size in MB from `information_schema.tables`
- Used to track disk usage over time

### 2. Insert Time
- Wall-clock latency for batch inserts
- Captures both foreground work and background contention

### 3. Delete Time
- Wall-clock latency for batch deletes
- Sensitive to index maintenance and merges

### 4. Index Page Merges
- Derived from `information_schema.innodb_metrics`
- Indicates background B-tree cleanup activity
- Important in steady-state workloads

### 5. Leaf Index Pages
- Number of leaf pages in the primary index
- Proxy for how data is laid out in the B-tree

### 6. Total Index Pages
- Includes both internal and leaf pages
- Indicates overall index footprint and memory pressure

> ⚠️ Page split metrics are intentionally excluded from conclusions while their accuracy is being validated.

---

## Why Index Page Merges Matter

Page merges occur after deletes when adjacent pages can be compacted.

They:
- Move records between pages
- Update parent nodes
- Consume CPU and buffer pool bandwidth

In long-running systems, **merge activity can dominate background cost**, even if insert rates remain constant.

---

## Key Observations

From the collected data:

- `AUTO_INCREMENT` performs best during the **initial growth phase**
- Random primary keys fragment early but **stabilize**
- Disk usage for random keys can become **smaller in steady-state**
- `AUTO_INCREMENT` tables show **significantly higher merge activity** over time
- Insert and delete latencies converge as the system matures

The results suggest that **primary key choice is phase-dependent**, not universally optimal.

---

## Repository Structure
.
├── script_test2.py # Main experiment driver
├── activity_file2.csv # Generated metrics (output)
├── mysql.txt # mysql queries to create tables/procs (output)
├── plots/ # Graphs and visualizations
├── README.md # This file


---

## Prerequisites

- MySQL 8.0+
- InnoDB storage engine
- Python 3.8+
- Python dependencies:
  ```bash
  pip install mysql-connector-python pandas matplotlib



