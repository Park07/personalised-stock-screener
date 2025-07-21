import os
import logging
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_postgres_user_connection():
    """Establishes a connection to the AWS RDS PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('RDS_HOST'),
            dbname=os.getenv('RDS_DB_NAME'),
            user=os.getenv('RDS_USERNAME'),
            password=os.getenv('RDS_PASSWORD'),
            port=os.getenv('RDS_PORT', '5432')
        )
        return conn
    except psycopg2.Error as e:
        logging.error(f"DATABASE CONNECTION ERROR: {e}")
        raise

def initialise_database():
    """Creates the 'users' table in the database if it doesn't exist."""
    conn = None
    try:
        conn = get_postgres_user_connection()
        cursor = conn.cursor()

        logging.info("Executing CREATE TABLE IF NOT EXISTS for 'users' table...")

        # SQL command to create the table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        conn.commit()
        logging.info(" 'users' table exists.")

    except psycopg2.Error as e:
        logging.error(f"Error initialising{e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Database connection closed.")

if __name__ == '__main__':
    initialise_database()
    logging.info("finished.")
