from sqlalchemy import create_engine, text
import os

class Credentials:
    def __init__(self):
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.database = os.getenv("POSTGRES_DB")

    def get_connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class ConnectionPostgres(Credentials):
    def __init__(self):
        super().__init__()
        self.engine = create_engine(self.get_connection_string())

    def get_engine(self):
        return self.engine

    def execute_query(self, query: str):
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            return result.fetchall()

    def close(self):
        self.engine.dispose()