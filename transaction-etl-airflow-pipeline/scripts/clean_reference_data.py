import psycopg2


from db_config import WAREHOUSE_DB

DB_CONFIG = WAREHOUSE_DB


def clean_reference_data():

    conn = psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()

    try:

        print("Starting cleaning...")

        # نفرغ نتائج التشغيل السابق
        cursor.execute("""
            TRUNCATE TABLE
                staging.departments_clean,
                staging.employees_clean,
                staging.employees_rejected;
        """)

        # -------------------------
        # تنظيف الإدارات
        # -------------------------
        cursor.execute("""
            INSERT INTO staging.departments_clean (
                department_id,
                department_name,
                sector,
                location,
                manager_employee_id,
                cost_center,
                active_flag
            )
            SELECT DISTINCT
                UPPER(TRIM(department_id)),
                TRIM(department_name),
                TRIM(sector),
                TRIM(location),
                UPPER(TRIM(manager_employee_id)),
                TRIM(cost_center),
                UPPER(TRIM(active_flag))
            FROM staging.departments_raw
            WHERE department_id IS NOT NULL;
        """)

        # -------------------------
        # الموظفين المرفوضين
        # -------------------------
        cursor.execute("""
            INSERT INTO staging.employees_rejected (
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
                source_updated_at,
                rejection_reason
            )
            SELECT
                e.employee_id,
                e.employee_name,
                e.department_id,
                e.job_title,
                e.hire_date,
                e.employment_status,
                e.grade,
                e.email,
                e.location,
                e.manager_employee_id,
                e.source_updated_at,
                CASE
                    WHEN e.department_id IS NULL
                        THEN 'MISSING_DEPARTMENT'

                    WHEN d.department_id IS NULL
                        THEN 'INVALID_DEPARTMENT'

                    WHEN e.hire_date > CURRENT_DATE
                        THEN 'FUTURE_HIRE_DATE'

                    ELSE 'UNKNOWN_ERROR'
                END
            FROM staging.employees_raw e

            LEFT JOIN staging.departments_clean d
                ON UPPER(TRIM(e.department_id)) = d.department_id

            WHERE
                   e.department_id IS NULL
                OR d.department_id IS NULL
                OR e.hire_date > CURRENT_DATE;
        """)

        # -------------------------
        # الموظفين الصحيحين
        # -------------------------
        cursor.execute("""
            INSERT INTO staging.employees_clean (
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

            WITH ranked_employees AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY employee_id
                        ORDER BY source_updated_at DESC
                    ) AS rn
                FROM staging.employees_raw
            )

            SELECT
                UPPER(TRIM(e.employee_id)),
                TRIM(e.employee_name),
                UPPER(TRIM(e.department_id)),
                TRIM(e.job_title),
                e.hire_date,

                CASE
                    WHEN LOWER(TRIM(e.employment_status)) = 'active'
                        THEN 'Active'

                    WHEN LOWER(TRIM(e.employment_status)) = 'inactive'
                        THEN 'Inactive'

                    WHEN LOWER(
                        REPLACE(
                            TRIM(e.employment_status),
                            '_',
                            ' '
                        )
                    ) = 'on leave'
                        THEN 'On Leave'

                    ELSE e.employment_status
                END,

                TRIM(e.grade),

                CASE
                    WHEN e.email LIKE '%@%.%'
                        THEN LOWER(TRIM(e.email))
                    ELSE NULL
                END,

                TRIM(e.location),
                UPPER(TRIM(e.manager_employee_id)),
                e.source_updated_at

            FROM ranked_employees e

            INNER JOIN staging.departments_clean d
                ON UPPER(TRIM(e.department_id)) = d.department_id

            WHERE
                e.rn = 1
                AND e.hire_date <= CURRENT_DATE;
        """)

        conn.commit()

        print("Cleaning completed successfully.")

    except Exception as error:

        conn.rollback()
        print(f"Cleaning failed: {error}")
        raise

    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":
    clean_reference_data()