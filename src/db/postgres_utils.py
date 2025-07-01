"""
PostgreSQL Database Utilities
Provides connection and query utilities for PostgreSQL database
"""
import os
import psycopg2
import psycopg2.extras
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()


class PostgreSQLConnection:
    """PostgreSQL connection utility class"""

    def __init__(self, db_url=None):
        self.db_url = db_url or os.environ.get("CHESS_TRAINER_DB_URL")
        if not self.db_url:
            raise ValueError(
                "CHESS_TRAINER_DB_URL environment variable not set")

        # Parse the URL to extract connection parameters
        parsed = urlparse(self.db_url)
        self.connection_params = {
            'host': parsed.hostname,
            'port': parsed.port,
            'database': parsed.path[1:],  # Remove leading '/'
            'user': parsed.username,
            'password': parsed.password
        }

    def get_connection(self):
        """Get a new PostgreSQL connection"""
        return psycopg2.connect(**self.connection_params)

    def execute_query(self, query, params=None, fetch=True):
        """Execute a query and optionally fetch results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    if query.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    else:
                        conn.commit()
                        return cursor.rowcount
                else:
                    conn.commit()
                    return cursor.rowcount

    def execute_many(self, query, params_list):
        """Execute a query multiple times with different parameters"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount

    def read_sql(self, query, params=None):
        """Read SQL query results into a pandas DataFrame"""
        with self.get_connection() as conn:
            return pd.read_sql(query, conn, params=params)

    def table_exists(self, table_name, schema='public'):
        """Check if a table exists"""
        query = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        );
        """
        result = self.execute_query(query, (schema, table_name))
        return result[0]['exists']


# Global instance for easy access
pg_conn = PostgreSQLConnection()


def get_postgres_connection():
    """Get a PostgreSQL connection using the global instance"""
    return pg_conn.get_connection()


def execute_postgres_query(query, params=None, fetch=True):
    """Execute a PostgreSQL query using the global instance"""
    return pg_conn.execute_query(query, params, fetch)


def read_postgres_sql(query, params=None):
    """Read PostgreSQL query results into a pandas DataFrame"""
    return pg_conn.read_sql(query, params)
