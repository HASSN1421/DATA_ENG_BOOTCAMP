-- Source DB simulator: 120k transactions + status history
DROP TABLE IF EXISTS source_transaction_status_history;
DROP TABLE IF EXISTS source_transactions;

CREATE TABLE source_transactions (
    source_row_id BIGSERIAL PRIMARY KEY,
    transaction_id TEXT,
    employee_id TEXT,
    transaction_type TEXT,
    classification TEXT,
    priority TEXT,
    channel TEXT,
    region_code TEXT,
    created_at TIMESTAMP,
    received_at TIMESTAMP,
    due_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    amount NUMERIC(12,2),
    is_escalated BOOLEAN,
    last_updated_at TIMESTAMP,
    source_system TEXT DEFAULT 'CORE_TXN_DB'
);

SELECT setseed(0.42);

INSERT INTO source_transactions (
    transaction_id, employee_id, transaction_type, classification, priority,
    channel, region_code, created_at, received_at, due_at, completed_at,
    status, amount, is_escalated, last_updated_at, source_system
)
SELECT
    CASE WHEN gs % 4000 = 0 THEN 'TXN-' || LPAD((gs-1)::text,7,'0')
         ELSE 'TXN-' || LPAD(gs::text,7,'0') END,
    CASE WHEN gs % 211 = 0 THEN NULL
         WHEN gs % 307 = 0 THEN 'EMP9999'
         ELSE 'EMP' || LPAD((1 + floor(random()*600))::int::text,4,'0') END,
    (ARRAY['طلب خدمة','معاملة مالية','بلاغ','طلب دعم','مراسلة','طلب اعتماد','استفسار'])[1 + floor(random()*7)::int],
    CASE WHEN gs % 503 = 0 THEN 'عاجل جدا'
         ELSE (ARRAY['عادي','سري','عاجل','داخلي','خارجي'])[1 + floor(random()*5)::int] END,
    (ARRAY['Low','Medium','High','Critical'])[1 + floor(random()*4)::int],
    (ARRAY['Portal','Email','Branch','API','Mobile'])[1 + floor(random()*5)::int],
    (ARRAY['R01','R02','R03','R04','R05'])[1 + floor(random()*5)::int],
    CASE WHEN gs % 2500 = 0 THEN TIMESTAMP '2027-01-01' + (random()*90) * INTERVAL '1 day'
         ELSE TIMESTAMP '2025-01-01' + (random()*620) * INTERVAL '1 day' END,
    NULL,NULL,NULL,NULL,NULL,NULL,NULL,'CORE_TXN_DB'
FROM generate_series(1,120000) gs;

UPDATE source_transactions
SET
    received_at = created_at + CASE WHEN source_row_id % 997 = 0
                                    THEN -(random()*2) * INTERVAL '1 day'
                                    ELSE (random()*8) * INTERVAL '1 hour' END,
    status = CASE WHEN source_row_id % 601 = 0 THEN 'قيد المعالجه'
                  WHEN source_row_id % 809 = 0 THEN 'مكتمل'
                  ELSE (ARRAY['مكتملة','قيد المعالجة','مرفوضة','محفوظة','معلقة','محالة'])[1 + floor(random()*6)::int] END,
    amount = CASE WHEN source_row_id % 431 = 0 THEN -ROUND((random()*5000)::numeric,2)
                  WHEN source_row_id % 223 = 0 THEN NULL
                  ELSE ROUND((50 + random()*20000)::numeric,2) END,
    is_escalated = (random() < 0.08);

UPDATE source_transactions
SET
    due_at = created_at + CASE WHEN priority='Critical' THEN INTERVAL '1 day'
                               WHEN priority='High' THEN INTERVAL '3 day'
                               WHEN priority='Medium' THEN INTERVAL '5 day'
                               ELSE INTERVAL '7 day' END,
    completed_at = CASE WHEN status IN ('مكتملة','مكتمل','مرفوضة','محفوظة')
                        THEN created_at + (random()*12) * INTERVAL '1 day' ELSE NULL END,
    last_updated_at = created_at + (random()*20) * INTERVAL '1 day';

UPDATE source_transactions SET completed_at = created_at - INTERVAL '2 day' WHERE source_row_id % 1201 = 0;
UPDATE source_transactions SET last_updated_at = created_at - INTERVAL '1 hour' WHERE source_row_id % 1601 = 0;

CREATE INDEX idx_source_transactions_last_updated ON source_transactions(last_updated_at);
CREATE INDEX idx_source_transactions_employee ON source_transactions(employee_id);
CREATE INDEX idx_source_transactions_created ON source_transactions(created_at);

CREATE TABLE source_transaction_status_history (
    history_id BIGSERIAL PRIMARY KEY,
    transaction_id TEXT,
    status_code TEXT,
    status_timestamp TIMESTAMP,
    changed_by TEXT,
    note TEXT
);

INSERT INTO source_transaction_status_history (
    transaction_id, status_code, status_timestamp, changed_by, note
)
SELECT
    t.transaction_id,
    CASE s.step_no
        WHEN 1 THEN 'RECEIVED'
        WHEN 2 THEN 'IN_PROGRESS'
        WHEN 3 THEN CASE WHEN t.status IN ('مكتملة','مكتمل') THEN 'COMPLETED'
                         WHEN t.status='مرفوضة' THEN 'REJECTED'
                         WHEN t.status='محفوظة' THEN 'SAVED'
                         WHEN t.status='معلقة' THEN 'ON_HOLD'
                         ELSE 'REFERRED' END
        ELSE 'FOLLOW_UP'
    END,
    t.created_at + (s.step_no * (0.5 + random()*2)) * INTERVAL '1 day'
        + CASE WHEN t.source_row_id % 1777 = 0 AND s.step_no=2 THEN -INTERVAL '3 day' ELSE INTERVAL '0 day' END,
    CASE WHEN random() < 0.02 THEN NULL
         ELSE 'EMP' || LPAD((1 + floor(random()*600))::int::text,4,'0') END,
    CASE WHEN random() < 0.01 THEN NULL ELSE 'Generated status event' END
FROM source_transactions t
CROSS JOIN LATERAL generate_series(1, 3 + floor(random()*2)::int) AS s(step_no);

CREATE INDEX idx_history_txn ON source_transaction_status_history(transaction_id);
CREATE INDEX idx_history_ts ON source_transaction_status_history(status_timestamp);

SELECT COUNT(*) AS transaction_rows FROM source_transactions;
SELECT COUNT(*) AS history_rows FROM source_transaction_status_history;
