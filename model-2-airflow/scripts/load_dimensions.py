import psycopg2


from db_config import WAREHOUSE_DB

DB_CONFIG = WAREHOUSE_DB


def load_dimensions():

    conn = psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()

    try:

        print("Loading departments dimension...")

        cursor.execute("""
            INSERT INTO dw.dim_department (
                department_id,
                department_name,
                sector,
                location,
                cost_center,
                active_flag
            )

            SELECT
                department_id,
                department_name,
                sector,
                location,
                cost_center,
                active_flag

            FROM staging.departments_clean

            ON CONFLICT (department_id)

            DO UPDATE SET
                department_name = EXCLUDED.department_name,
                sector = EXCLUDED.sector,
                location = EXCLUDED.location,
                cost_center = EXCLUDED.cost_center,
                active_flag = EXCLUDED.active_flag;
        """)


        print("Loading employees dimension...")

        cursor.execute("""
            INSERT INTO dw.dim_employee (
                employee_id,
                employee_name,
                department_key,
                job_title,
                hire_date,
                employment_status,
                grade,
                email,
                location
            )

            SELECT
                e.employee_id,
                e.employee_name,
                d.department_key,
                e.job_title,
                e.hire_date,
                e.employment_status,
                e.grade,
                e.email,
                e.location

            FROM staging.employees_clean e

            INNER JOIN dw.dim_department d
                ON e.department_id = d.department_id

            ON CONFLICT (employee_id)

            DO UPDATE SET
                employee_name = EXCLUDED.employee_name,
                department_key = EXCLUDED.department_key,
                job_title = EXCLUDED.job_title,
                hire_date = EXCLUDED.hire_date,
                employment_status = EXCLUDED.employment_status,
                grade = EXCLUDED.grade,
                email = EXCLUDED.email,
                location = EXCLUDED.location;
        """)

        conn.commit()

        print("Dimensions loaded successfully.")

    except Exception as error:

        conn.rollback()

        print(f"Dimensions loading failed: {error}")

        raise

    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":
    load_dimensions()