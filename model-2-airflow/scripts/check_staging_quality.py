import psycopg2
from db_config import WAREHOUSE_DB

DB_CONFIG = WAREHOUSE_DB

CHECKS = {

    # =====================================================
    # Employees
    # =====================================================

    "duplicate_employee_ids": """
        SELECT COUNT(*)
        FROM (
            SELECT employee_id
            FROM staging.employees_raw
            GROUP BY employee_id
            HAVING COUNT(*) > 1
        ) x;
    """,

    "employees_missing_department": """
        SELECT COUNT(*)
        FROM staging.employees_raw
        WHERE department_id IS NULL;
    """,

    "employees_invalid_department": """
        SELECT COUNT(*)
        FROM staging.employees_raw e
        LEFT JOIN staging.departments_raw d
            ON e.department_id = d.department_id
        WHERE e.department_id IS NOT NULL
          AND d.department_id IS NULL;
    """,

    "employees_bad_email": """
        SELECT COUNT(*)
        FROM staging.employees_raw
        WHERE email IS NULL
           OR email NOT LIKE '%@%.%';
    """,

    "employees_future_hire_date": """
        SELECT COUNT(*)
        FROM staging.employees_raw
        WHERE hire_date > CURRENT_DATE;
    """,

    "employees_non_standard_status": """
        SELECT COUNT(*)
        FROM staging.employees_raw
        WHERE employment_status NOT IN (
            'Active',
            'Inactive',
            'On Leave'
        );
    """,


    # =====================================================
    # Transactions
    # =====================================================

    "duplicate_transaction_ids": """
        SELECT COUNT(*)
        FROM (
            SELECT transaction_id
            FROM staging.transactions_raw
            GROUP BY transaction_id
            HAVING COUNT(*) > 1
        ) x;
    """,

    "transactions_missing_employee": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE employee_id IS NULL;
    """,

    "transactions_unknown_employee": """
        WITH employees AS (
            SELECT DISTINCT employee_id
            FROM staging.employees_raw
            WHERE employee_id IS NOT NULL
        )
        SELECT COUNT(*)
        FROM staging.transactions_raw t
        LEFT JOIN employees e
            ON t.employee_id = e.employee_id
        WHERE t.employee_id IS NOT NULL
          AND e.employee_id IS NULL;
    """,

    "transactions_negative_amount": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE amount < 0;
    """,

    "transactions_null_amount": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE amount IS NULL;
    """,

    "received_before_created": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE received_at < created_at;
    """,

    "completed_before_created": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE completed_at < created_at;
    """,

    "updated_before_created": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE last_updated_at < created_at;
    """,

    "future_transactions": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE created_at > CURRENT_TIMESTAMP;
    """,

    "non_standard_transaction_status": """
        SELECT COUNT(*)
        FROM staging.transactions_raw
        WHERE status NOT IN (
            'مكتملة',
            'قيد المعالجة',
            'مرفوضة',
            'محفوظة',
            'معلقة',
            'محالة'
        );
    """
}
def run_quality_checks():
    conn=psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()

    print("=" * 60)
    print("STAGING DATA QUALITY REPORT")
    print("=" * 60)

    try:

        total_issues = 0

        for check_name, query in CHECKS.items():

            cursor.execute(query)

            count = cursor.fetchone()[0]

            total_issues += count

            print(
                f"{check_name:<40} : {count}"
            )

        print("=" * 60)
        print(f"Total detected issues: {total_issues}")
        print("=" * 60)

    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":

    run_quality_checks()
      
