CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS staging.transactions_raw (
    source_row_id BIGINT, transaction_id TEXT, employee_id TEXT, transaction_type TEXT,
    classification TEXT, priority TEXT, channel TEXT, region_code TEXT,
    created_at TIMESTAMP, received_at TIMESTAMP, due_at TIMESTAMP, completed_at TIMESTAMP,
    status TEXT, amount NUMERIC(12,2), is_escalated BOOLEAN,
    last_updated_at TIMESTAMP, source_system TEXT
);

CREATE TABLE IF NOT EXISTS staging.employees_raw (
    employee_id TEXT, employee_name TEXT, department_id TEXT, job_title TEXT,
    hire_date DATE, employment_status TEXT, grade TEXT, email TEXT,
    location TEXT, manager_employee_id TEXT, source_updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.departments_raw (
    department_id TEXT, department_name TEXT, sector TEXT, location TEXT,
    manager_employee_id TEXT, cost_center TEXT, active_flag TEXT
);

CREATE TABLE IF NOT EXISTS dw.dim_department (
    department_key BIGSERIAL PRIMARY KEY, department_id TEXT UNIQUE,
    department_name TEXT, sector TEXT, location TEXT, cost_center TEXT, active_flag TEXT
);

CREATE TABLE IF NOT EXISTS dw.dim_employee (
    employee_key BIGSERIAL PRIMARY KEY, employee_id TEXT UNIQUE,
    employee_name TEXT, department_key BIGINT REFERENCES dw.dim_department(department_key),
    job_title TEXT, hire_date DATE, employment_status TEXT, grade TEXT,
    email TEXT, location TEXT
);

CREATE TABLE IF NOT EXISTS dw.fact_transactions (
    transaction_key BIGSERIAL PRIMARY KEY, transaction_id TEXT,
    employee_key BIGINT REFERENCES dw.dim_employee(employee_key),
    department_key BIGINT REFERENCES dw.dim_department(department_key),
    transaction_type TEXT, classification TEXT, priority TEXT, channel TEXT,
    region_code TEXT, created_at TIMESTAMP, due_at TIMESTAMP, completed_at TIMESTAMP,
    status TEXT, amount NUMERIC(12,2), is_escalated BOOLEAN,
    cycle_hours NUMERIC(12,2), sla_breached BOOLEAN,
    source_system TEXT, last_updated_at TIMESTAMP
);
