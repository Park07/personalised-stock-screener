#!/usr/bin/env python3
import psycopg2
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    try:
        print("🔌 Testing RDS PostgreSQL connection...")
        print(f"📍 Host: {os.getenv('RDS_HOST')}")
        print(f"🚪 Port: {os.getenv('RDS_PORT')}")
        print(f"🗄️  Database: {os.getenv('RDS_DB_NAME')}")
        print(f"👤 Username: {os.getenv('RDS_USERNAME')}")

        conn = psycopg2.connect(
            host=os.getenv('RDS_HOST'),
            port=os.getenv('RDS_PORT', 5432),
            database=os.getenv('RDS_DB_NAME', 'postgres'),
            user=os.getenv('RDS_USERNAME'),
            password=os.getenv('RDS_PASSWORD')
        )

        cursor = conn.cursor()

        # Test basic connection
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"✅ Connected successfully!")
        print(f"📊 PostgreSQL version: {version[0]}")

        # Check existing databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        print(f"🗃️  Available databases: {[db[0] for db in databases]}")

        cursor.close()
        conn.close()
        print("🎉 Connection test completed successfully!")

        return True

    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        if "timeout expired" in str(e):
            print("💡 This might be a firewall/security group issue")
        elif "authentication failed" in str(e):
            print("💡 Check your username and password")
        elif "could not connect to server" in str(e):
            print("💡 Check your host and port, and security group settings")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)