The project was developed as part of my Data Engineering learning journey and is inspired by the orchestration concepts covered in the DataTalks.Club Data Engineering Zoomcamp, with additional implementation and customization around data quality, dimensional modeling, incremental loading, watermarking, and validation.

---

## Project Overview

The pipeline processes transaction data from multiple sources and loads clean, validated data into a PostgreSQL Data Warehouse.

The project covers:

Source Systems → Extraction → Staging → Data Quality → Transformation → Dimensions & Facts → Validation

The goal was to simulate a realistic Data Engineering workflow rather than only execute individual Airflow tasks.

---

## Architecture

```text
PostgreSQL Source
     +
Excel Reference Data
     |
     v
Apache Airflow
     |
     v
Extraction Layer
     |
     v
Staging Tables
     |
     v
Data Quality Checks
     |
     v
Cleaning & Transformation
     |
     v
Dimension Tables
     |
     +---- dim_employee
     |
     +---- dim_department
     |
     v
Fact Table
     |
     +---- fact_transactions
     |
     v
Final Validation
     |
     v
PostgreSQL Data Warehouse

Tech Stack
- Apache Airflow
- Python
- PostgreSQL
- SQL
- Docker
- Docker Compose
- Pandas
- Excel
- pgAdmin
Data Sources
The project uses two types of source data.
PostgreSQL
The transactional source contains business transaction records including:
- Transaction ID
- Employee ID
- Transaction type
- Classification
- Priority
- Channel
- Region
- Status
- Amount
- Created / received / due / completed timestamps
- Last updated timestamp
Excel
Excel is used as a reference source for:
- Employees
- Departments
The dataset also contains intentionally introduced data quality issues to simulate real pipeline validation and cleaning scenarios.
ETL Workflow
The Airflow DAG orchestrates multiple Python scripts instead of placing all transformation logic directly inside the DAG.
extract_transactions
        |
        v
extract_excel
        |
        v
check_staging_quality
        |
        v
clean_reference_data
        |
        v
clean_transactions
        |
        v
load_dimensions
        |
        v
load_fact
        |
        v
final_validation

This keeps the Airflow DAG focused on orchestration while the Python scripts handle the actual ETL logic.
Staging Layer
Extracted data is first loaded into staging tables before being transformed.
Examples:
staging.transactions_raw
staging.employees_raw
staging.departments_raw

The staging layer separates source data from the final Data Warehouse models and provides a controlled area for validation and transformation.
Data Quality
The pipeline includes data quality checks before loading data into the final warehouse.
Examples of validation include:
Duplicate transaction IDs
Missing employee IDs
Invalid department references
Unexpected status values
Negative or missing amounts
Invalid timestamps
Future dates
Invalid employee records

Invalid data can be separated from valid data before loading into the final Fact and Dimension tables.
Data Warehouse Model
The final analytical model follows a dimensional approach.
                dim_employee
                     |
                     |
dim_department ---- fact_transactions

Dimension Tables
dw.dim_employee
dw.dim_department

Fact Table
dw.fact_transactions

The Fact table represents transaction events while the Dimension tables provide descriptive employee and department information.
Incremental Loading
The pipeline was initially implemented as a full-load process and later enhanced to support incremental loading.
Instead of processing the entire source every time, the pipeline extracts only records that have changed since the previous successful run.
The main tracking column is:
last_updated_at

The pipeline stores its progress in:
dw.etl_control

using:
last_successful_watermark
last_successful_run

The extraction window is conceptually:
last_successful_watermark
        <
last_updated_at
        <=
current_run_upper_bound

This prevents the pipeline from repeatedly processing the full dataset.
Watermark Strategy
The watermark represents the last successfully processed point in the source system.
An important design decision in this project is that the watermark is updated only after the pipeline completes successfully.
Extract
   |
Transform
   |
Load
   |
Validate
   |
Success?
   |
   +---- Yes → Update watermark
   |
   +---- No  → Keep previous watermark

This reduces the risk of losing data if a pipeline fails in the middle of execution.
UPSERT Strategy
The final Fact table uses an UPSERT approach during incremental loads.
Conceptually:
New transaction
    → INSERT

Existing transaction changed
    → UPDATE

Unchanged transaction
    → No unnecessary reload

This allows the warehouse to handle both newly created records and updates to existing transactions.
Backfill vs Incremental Load
The project also explores the difference between normal incremental processing and historical backfills.
Incremental
Used during normal scheduled execution.
Process records changed since the last successful watermark.

Backfill
Used when a specific historical period needs to be reprocessed.
start_date
    →
end_date

Backfill runs should not modify the normal incremental watermark.
Airflow Catchup
A separate learning DAG was used to understand Airflow Catchup behavior.
Catchup automatically creates missing scheduled runs for previous intervals.
This helped clarify the difference between:
Schedule
    = When a DAG should run

Catchup
    = Automatically create missed scheduled runs

Backfill
    = Intentionally reprocess a historical period

Final Results
After cleaning and validation, the Data Warehouse contains approximately:
112,680 validated transaction records

with supporting Employee and Department dimensions.
The project demonstrates the complete movement of data from operational sources into an analytical warehouse.
Project Structure
model-2-airflow/
│
├── dags/
│   └── transactions_etl_pipeline.py
│
├── scripts/
│   ├── extract_transactions.py
│   ├── extract_excel.py
│   ├── check_staging_quality.py
│   ├── clean_reference_data.py
│   ├── clean_transactions.py
│   ├── load_dimensions.py
│   ├── load_fact.py
│   └── final_validation.py
│
├── sql/
│   ├── setup_source_db.sql
│   └── create_warehouse_schema.sql
│
├── examples/
│   └── learning/
│
├── Dockerfile
├── docker-compose.yaml
└── README.md

Running the Project
Start the Docker environment:
docker compose up -d

Check the containers:
docker compose ps

Open the Airflow web interface and run:
transactions_etl_pipeline

The DAG will orchestrate the extraction, transformation, loading, and validation steps.
Key Concepts Practiced
ETL
Data Pipelines
Workflow Orchestration
Apache Airflow DAGs
Docker
PostgreSQL
Staging
Data Quality
Dimensional Modeling
Fact & Dimension Tables
Incremental Loading
Watermarking
UPSERT
Backfill
Catchup
Retry
Pipeline Validation

Learning Reference
This project was developed as part of my Data Engineering learning journey.
The Apache Airflow and orchestration concepts were based on the:
Data Engineering Zoomcamp — DataTalks.Club
I extended the learning material by building a customized transaction-processing pipeline with multiple data sources, data quality validation, dimensional modeling, incremental loading, watermark management, and UPSERT logic.
```
