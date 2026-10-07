import psycopg2
from psycopg2.extras import execute_values


from db_config import SOURCE_DB, WAREHOUSE_DB

def extract_incremental_transactions():

    source_conn = psycopg2.connect(**SOURCE_DB)
    warehouse_conn = psycopg2.connect(**WAREHOUSE_DB)

    source_cursor = source_conn.cursor(
        name="transactions_cursor"
    )

    warehouse_cursor = warehouse_conn.cursor()

    try:

        print("Starting incremental extraction...")


        # ==========================================
        # 1. Read last successful watermark
        # ==========================================

        warehouse_cursor.execute("""
            SELECT last_successful_watermark
            FROM dw.etl_control
            WHERE pipeline_name = 'transactions_pipeline';
        """)

        result = warehouse_cursor.fetchone()

        if result is None:
            raise Exception(
                "Watermark not found in dw.etl_control"
            )

        last_watermark = result[0]

        print(
            f"Last successful watermark: {last_watermark}"
        )


        # ==========================================
        # 2. Define upper bound for this run
        # ==========================================

        temp_cursor = source_conn.cursor()

        temp_cursor.execute("""
            SELECT CURRENT_TIMESTAMP::timestamp;
        """)

        current_run = temp_cursor.fetchone()[0]

        temp_cursor.close()

        print(
            f"Current run upper bound: {current_run}"
        )


        # ==========================================
        # 3. Clear current staging batch
        # ==========================================

        warehouse_cursor.execute("""
            TRUNCATE TABLE staging.transactions_raw;
        """)

        warehouse_conn.commit()


        # ==========================================
        # 4. Extract only new / changed rows
        # ==========================================

        query = """
            SELECT
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

            FROM source_transactions

            WHERE last_updated_at > %s
              AND last_updated_at <= %s

            ORDER BY last_updated_at;
        """


        source_cursor.execute(
            query,
            (
                last_watermark,
                current_run
            )
        )


        # ==========================================
        # 5. Insert current batch into staging
        # ==========================================

        insert_query = """
            INSERT INTO staging.transactions_raw (
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
            VALUES %s
        """


        batch_size = 5000
        total_loaded = 0


        while True:

            rows = source_cursor.fetchmany(
                batch_size
            )

            if not rows:
                break


            execute_values(
                warehouse_cursor,
                insert_query,
                rows,
                page_size=batch_size
            )

            warehouse_conn.commit()

            total_loaded += len(rows)

            print(
                f"Loaded {total_loaded} rows..."
            )


        print("--------------------------------")
        print("Incremental extraction completed.")
        print(f"Rows extracted: {total_loaded}")
        print("--------------------------------")


    except Exception as error:

        warehouse_conn.rollback()

        print(
            f"Incremental extraction failed: {error}"
        )

        raise


    finally:

        source_cursor.close()
        warehouse_cursor.close()

        source_conn.close()
        warehouse_conn.close()


if __name__ == "__main__":

    extract_incremental_transactions()