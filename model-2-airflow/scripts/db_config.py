import os


WAREHOUSE_DB = {
    "host": "warehouse-db",
    "port": 5432,
    "dbname": os.getenv("WAREHOUSE_DB"),
    "user": os.getenv("WAREHOUSE_USER"),
    "password": os.getenv("WAREHOUSE_PASSWORD"),
}


SOURCE_DB = {
    "host": "source-db",
    "port": 5432,
    "dbname": os.getenv("SOURCE_DB_NAME"),
    "user": os.getenv("SOURCE_DB_USER"),
    "password": os.getenv("SOURCE_DB_PASSWORD"),
}