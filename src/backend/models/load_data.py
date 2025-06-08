from pathlib import Path
import hashlib
import os
import sys
import pandas as pd
import psycopg2

sys.path.append(os.path.join(str(Path(__file__).resolve().parents[2])))
from src.backend.models.conn_db import ConnectionPostgres

class Credentials:
    def __init__(self):
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.database = os.getenv("POSTGRES_DB")

    def conn(self):
        return psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            port=self.port
        )


class LoadData(Credentials):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df
        self.table_name = 'reagendados_hoje'
        self.connection = self.conn()
        self.cursor = self.connection.cursor()
        self.columns = df.columns.tolist()
        self.engine = ConnectionPostgres().get_engine()
        
    def create_table_schema(self):
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.table_name};")
        
        columns = ", ".join([f'"{col}" VARCHAR(255)' for col in self.columns])
        self.cursor.execute(f"""
            CREATE TABLE {self.table_name} (
                id SERIAL PRIMARY KEY,
                {columns}
            )
        """)
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def insert(self):
        self.create_table_schema()
        self.df.to_sql(self.table_name, self.engine, if_exists='replace', index=False)

        self.engine.dispose()
