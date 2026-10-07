import psycopg2


from db_config import WAREHOUSE_DB

DB_CONFIG = WAREHOUSE_DB


def clean_transactions():

    conn = psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()

    try:

        print("Starting transactions cleaning...")

        # تنظيف نتائج التشغيل السابق
        cursor.execute("""
            TRUNCATE TABLE
                staging.transactions_clean,
                staging.transactions_rejected;
        """)


        # =====================================
        # REJECTED TRANSACTIONS
        # =====================================

        print("Finding rejected transactions...")

        cursor.execute("""
            INSERT INTO staging.transactions_rejected (
                source_row_id,
                transaction_id,
                employee_id,
                transaction_type,
                classification,
                priority,
                channel,
                region_code,
                created_at,
                received_at,
                due_at,
                completed_at,
                status,
                amount,
                is_escalated,
                last_updated_at,
                source_system,
                rejection_reason
            )

            WITH ranked AS (

                SELECT
                    t.*,

                    ROW_NUMBER() OVER (
                        PARTITION BY transaction_id
                        ORDER BY last_updated_at DESC
                    ) AS rn

                FROM staging.transactions_raw t
            )

            SELECT
                t.source_row_id,
                t.transaction_id,
                t.employee_id,
                t.transaction_type,
                t.classification,
                t.priority,
                t.channel,
                t.region_code,
                t.created_at,
                t.received_at,
                t.due_at,
                t.completed_at,
                t.status,
                t.amount,
                t.is_escalated,
                t.last_updated_at,
                t.source_system,

                CASE

                    WHEN t.transaction_id IS NULL
                        THEN 'MISSING_TRANSACTION_ID'

                    WHEN t.rn > 1
                        THEN 'DUPLICATE_TRANSACTION'

                    WHEN t.employee_id IS NULL
                        THEN 'MISSING_EMPLOYEE'

                    WHEN e.employee_id IS NULL
                        THEN 'UNKNOWN_EMPLOYEE'

                    WHEN t.amount IS NULL
                        THEN 'NULL_AMOUNT'

                    WHEN t.amount < 0
                        THEN 'NEGATIVE_AMOUNT'

                    WHEN t.received_at < t.created_at
                        THEN 'RECEIVED_BEFORE_CREATED'

                    WHEN t.completed_at < t.created_at
                        THEN 'COMPLETED_BEFORE_CREATED'

                    WHEN t.last_updated_at < t.created_at
                        THEN 'UPDATED_BEFORE_CREATED'

                    WHEN t.created_at > CURRENT_TIMESTAMP
                        THEN 'FUTURE_TRANSACTION'

                    ELSE 'UNKNOWN_ERROR'

                END

            FROM ranked t

            LEFT JOIN staging.employees_clean e
                ON UPPER(TRIM(t.employee_id))
                 = e.employee_id

            WHERE
                   t.transaction_id IS NULL
                OR t.rn > 1
                OR t.employee_id IS NULL
                OR e.employee_id IS NULL
                OR t.amount IS NULL
                OR t.amount < 0
                OR t.received_at < t.created_at
                OR t.completed_at < t.created_at
                OR t.last_updated_at < t.created_at
                OR t.created_at > CURRENT_TIMESTAMP;
        """)


        # =====================================
        # CLEAN TRANSACTIONS
        # =====================================

        print("Cleaning valid transactions...")

        cursor.execute("""
            INSERT INTO staging.transactions_clean (
                source_row_id,
                transaction_id,
                employee_id,
                transaction_type,
                classification,
                priority,
                channel,
                region_code,
                created_at,
                received_at,
                due_at,
                completed_at,
                status,
                amount,
                is_escalated,
                last_updated_at,
                source_system
            )

            WITH ranked AS (

                SELECT
                    t.*,

                    ROW_NUMBER() OVER (
                        PARTITION BY transaction_id
                        ORDER BY last_updated_at DESC
                    ) AS rn

                FROM staging.transactions_raw t
            )

            SELECT
                t.source_row_id,

                UPPER(TRIM(t.transaction_id)),

                UPPER(TRIM(t.employee_id)),

                TRIM(t.transaction_type),

                CASE
                    WHEN TRIM(t.classification) = 'عاجل جدا'
                        THEN 'عاجل'
                    ELSE TRIM(t.classification)
                END,

                TRIM(t.priority),
                TRIM(t.channel),
                TRIM(t.region_code),

                t.created_at,
                t.received_at,
                t.due_at,
                t.completed_at,

                CASE
                    WHEN TRIM(t.status) = 'مكتمل'
                        THEN 'مكتملة'

                    WHEN TRIM(t.status) = 'قيد المعالجه'
                        THEN 'قيد المعالجة'

                    ELSE TRIM(t.status)
                END,

                t.amount,
                t.is_escalated,
                t.last_updated_at,
                t.source_system

            FROM ranked t

            INNER JOIN staging.employees_clean e
                ON UPPER(TRIM(t.employee_id))
                 = e.employee_id

            WHERE
                t.rn = 1

                AND t.transaction_id IS NOT NULL

                AND t.employee_id IS NOT NULL

                AND t.amount IS NOT NULL

                AND t.amount >= 0

                AND (
                    t.received_at IS NULL
                    OR t.received_at >= t.created_at
                )

                AND (
                    t.completed_at IS NULL
                    OR t.completed_at >= t.created_at
                )

                AND t.last_updated_at >= t.created_at

                AND t.created_at <= CURRENT_TIMESTAMP;
        """)


        conn.commit()

        print("Transactions cleaning completed successfully.")


    except Exception as error:

        conn.rollback()

        print(f"Transactions cleaning failed: {error}")

        raise


    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":
    clean_transactions()