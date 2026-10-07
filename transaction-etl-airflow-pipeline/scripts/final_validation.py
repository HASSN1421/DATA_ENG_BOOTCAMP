import psycopg2


from db_config import WAREHOUSE_DB

DB_CONFIG = WAREHOUSE_DB

def final_validation():

    conn = psycopg2.connect(**WAREHOUSE_DB)
    cursor = conn.cursor()

    try:

        print("Starting final validation...")


        # ==========================================
        # 1. عدد سجلات الـ Batch الخام
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM staging.transactions_raw;
        """)

        raw_count = cursor.fetchone()[0]


        # ==========================================
        # 2. عدد السجلات النظيفة
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM staging.transactions_clean;
        """)

        clean_count = cursor.fetchone()[0]


        # ==========================================
        # 3. عدد السجلات المرفوضة
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM staging.transactions_rejected;
        """)

        rejected_count = cursor.fetchone()[0]


        # ==========================================
        # 4. التأكد أن Clean Batch وصلت إلى Fact
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)

            FROM staging.transactions_clean t

            INNER JOIN dw.fact_transactions f
                ON t.transaction_id = f.transaction_id;
        """)

        loaded_batch_count = cursor.fetchone()[0]


        # ==========================================
        # 5. إجمالي Fact التاريخية
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM dw.fact_transactions;
        """)

        total_fact_count = cursor.fetchone()[0]


        # ==========================================
        # 6. التأكد من عدم وجود معاملات مكررة
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT transaction_id

                FROM dw.fact_transactions

                GROUP BY transaction_id

                HAVING COUNT(*) > 1
            ) x;
        """)

        duplicate_count = cursor.fetchone()[0]


        # ==========================================
        # 7. Dimensions
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM dw.dim_employee;
        """)

        employee_count = cursor.fetchone()[0]


        cursor.execute("""
            SELECT COUNT(*)
            FROM dw.dim_department;
        """)

        department_count = cursor.fetchone()[0]


        # ==========================================
        # Report
        # ==========================================

        print("--------------------------------------")
        print(f"Raw Batch          : {raw_count}")
        print(f"Clean Batch        : {clean_count}")
        print(f"Rejected Batch     : {rejected_count}")
        print(f"Loaded From Batch  : {loaded_batch_count}")
        print(f"Total Fact History : {total_fact_count}")
        print(f"Employees          : {employee_count}")
        print(f"Departments        : {department_count}")
        print(f"Duplicate TXNs     : {duplicate_count}")
        print("--------------------------------------")


        # ==========================================
        # Validation Rules
        # ==========================================

        if employee_count == 0:
            raise Exception(
                "DIM_EMPLOYEE_IS_EMPTY"
            )


        if department_count == 0:
            raise Exception(
                "DIM_DEPARTMENT_IS_EMPTY"
            )


        if duplicate_count > 0:
            raise Exception(
                f"DUPLICATE_TRANSACTIONS_FOUND: {duplicate_count}"
            )


        # كل سجل Clean لازم يكون موجود في Fact
        if clean_count != loaded_batch_count:
            raise Exception(
                f"BATCH_COUNT_MISMATCH: "
                f"clean={clean_count}, "
                f"loaded={loaded_batch_count}"
            )


        # Raw المفروض تتوزع بين Clean و Rejected
        if raw_count != clean_count + rejected_count:
            raise Exception(
                f"BATCH_ACCOUNTING_ERROR: "
                f"raw={raw_count}, "
                f"clean={clean_count}, "
                f"rejected={rejected_count}"
            )


        print("Validation passed successfully.")


        # ==========================================
        # 8. Update Watermark
        # ==========================================

        cursor.execute("""
            SELECT MAX(last_updated_at)
            FROM staging.transactions_raw;
        """)

        new_watermark = cursor.fetchone()[0]


        # لو عندنا Batch جديدة
        if new_watermark is not None:

            cursor.execute("""
                UPDATE dw.etl_control

                SET
                    last_successful_watermark = %s,
                    last_successful_run = CURRENT_TIMESTAMP

                WHERE pipeline_name =
                    'transactions_pipeline';
            """, (new_watermark,))


            if cursor.rowcount == 0:
                raise Exception(
                    "ETL_CONTROL_RECORD_NOT_FOUND"
                )


            print(
                f"Watermark updated to: {new_watermark}"
            )


        # لو ما فيه بيانات جديدة
        else:

            cursor.execute("""
                UPDATE dw.etl_control

                SET
                    last_successful_run =
                        CURRENT_TIMESTAMP

                WHERE pipeline_name =
                    'transactions_pipeline';
            """)

            print(
                "No new transactions."
            )

            print(
                "Watermark remains unchanged."
            )


        conn.commit()

        print(
            "Final validation completed successfully."
        )


    except Exception as error:

        conn.rollback()

        print(
            f"Final validation failed: {error}"
        )

        raise


    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":

    final_validation()