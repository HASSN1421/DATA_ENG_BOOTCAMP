import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


# مسار ملف Excel داخل Airflow Container
EXCEL_PATH = "/opt/airflow/data/employees_departments.xlsx"


# اتصال الـ Data Warehouse
from db_config import WAREHOUSE_DB

DB_CONFIG = WAREHOUSE_DB


# تحويل NaN / NaT القادمة من Excel إلى NULL
def clean_value(value):

    if pd.isna(value):
        return None

    # تحويل pandas Timestamp إلى Python datetime
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    return value


# =========================================================
# Employees
# =========================================================

def load_employees():

    print("Reading Employees sheet...")

    employees = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Employees"
    )

    print(f"Employees extracted: {len(employees)}")

    # تحويل كل سجل إلى tuple وتنظيف القيم الفارغة
    rows = []

    for row in employees.itertuples(index=False, name=None):

        cleaned_row = tuple(
            clean_value(value)
            for value in row
        )

        rows.append(cleaned_row)


    conn = psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()

    try:

        # لأننا الآن نعمل Full Load للـ staging
        cursor.execute(
            "TRUNCATE TABLE staging.employees_raw;"
        )


        insert_query = """
            INSERT INTO staging.employees_raw (
                employee_id,
                employee_name,
                department_id,
                job_title,
                hire_date,
                employment_status,
                grade,
                email,
                location,
                manager_employee_id,
                source_updated_at
            )
            VALUES %s
        """


        execute_values(
            cursor,
            insert_query,
            rows,
            page_size=1000
        )


        conn.commit()

        print(
            f"Employees loaded successfully: {len(rows)}"
        )


    except Exception as error:

        conn.rollback()

        print(
            f"Employees load failed: {error}"
        )

        raise


    finally:

        cursor.close()
        conn.close()


# =========================================================
# Departments
# =========================================================

def load_departments():

    print("Reading Departments sheet...")

    departments = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Departments"
    )

    print(
        f"Departments extracted: {len(departments)}"
    )


    rows = []

    for row in departments.itertuples(index=False, name=None):

        cleaned_row = tuple(
            clean_value(value)
            for value in row
        )

        rows.append(cleaned_row)


    conn = psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()


    try:

        cursor.execute(
            "TRUNCATE TABLE staging.departments_raw;"
        )


        insert_query = """
            INSERT INTO staging.departments_raw (
                department_id,
                department_name,
                sector,
                location,
                manager_employee_id,
                cost_center,
                active_flag
            )
            VALUES %s
        """


        execute_values(
            cursor,
            insert_query,
            rows,
            page_size=1000
        )


        conn.commit()


        print(
            f"Departments loaded successfully: {len(rows)}"
        )


    except Exception as error:

        conn.rollback()

        print(
            f"Departments load failed: {error}"
        )

        raise


    finally:

        cursor.close()
        conn.close()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    load_employees()

    load_departments()

    print(
        "Excel extraction completed successfully."
    )