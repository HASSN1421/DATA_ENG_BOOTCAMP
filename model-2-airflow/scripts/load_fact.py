import psycopg2


from db_config import WAREHOUSE_DB

DB_CONFIG = WAREHOUSE_DB

def load_fact():

    conn = psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()

    try:

        print("Starting incremental load to fact_transactions...")


        cursor.execute("""
            INSERT INTO dw.fact_transactions (
                transaction_id,
                employee_key,
                department_key,
                transaction_type,
                classification,
                priority,
                channel,
                region_code,
                created_at,
                due_at,
                completed_at,
                status,
                amount,
                is_escalated,
                cycle_hours,
                sla_breached,
                source_system,
                last_updated_at
            )

            SELECT
                t.transaction_id,
                e.employee_key,
                e.department_key,
                t.transaction_type,
                t.classification,
                t.priority,
                t.channel,
                t.region_code,
                t.created_at,
                t.due_at,
                t.completed_at,
                t.status,
                t.amount,
                t.is_escalated,

                CASE
                    WHEN t.completed_at IS NOT NULL
                    THEN ROUND(
                        (
                            EXTRACT(
                                EPOCH FROM (
                                    t.completed_at - t.created_at
                                )
                            ) / 3600
                        )::numeric,
                        2
                    )
                    ELSE NULL
                END AS cycle_hours,

                CASE
                    WHEN t.due_at IS NULL
                    THEN NULL

                    WHEN t.completed_at IS NOT NULL
                    THEN t.completed_at > t.due_at

                    ELSE CURRENT_TIMESTAMP > t.due_at
                END AS sla_breached,

                t.source_system,
                t.last_updated_at

            FROM staging.transactions_clean t

            INNER JOIN dw.dim_employee e
                ON t.employee_id = e.employee_id


            ON CONFLICT (transaction_id)

            DO UPDATE SET
                employee_key = EXCLUDED.employee_key,
                department_key = EXCLUDED.department_key,
                transaction_type = EXCLUDED.transaction_type,
                classification = EXCLUDED.classification,
                priority = EXCLUDED.priority,
                channel = EXCLUDED.channel,
                region_code = EXCLUDED.region_code,
                created_at = EXCLUDED.created_at,
                due_at = EXCLUDED.due_at,
                completed_at = EXCLUDED.completed_at,
                status = EXCLUDED.status,
                amount = EXCLUDED.amount,
                is_escalated = EXCLUDED.is_escalated,
                cycle_hours = EXCLUDED.cycle_hours,
                sla_breached = EXCLUDED.sla_breached,
                source_system = EXCLUDED.source_system,
                last_updated_at = EXCLUDED.last_updated_at;
        """)


        affected_rows = cursor.rowcount

        conn.commit()

        print("Fact incremental load completed successfully.")
        print(f"Rows inserted or updated: {affected_rows}")


    except Exception as error:

        conn.rollback()

        print(f"Fact incremental load failed: {error}")

        raise


    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":
    load_fact()