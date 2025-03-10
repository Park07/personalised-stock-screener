import psycopg2

db_host = 'foxtrot-db.cialrzbfckl9.us-east-1.rds.amazonaws.com'
db_name = 'postgres' 
db_user = 'foxtrot'
db_password = 'FiveGuys'  

# Connect to the database
try:
    print("hi")
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password
    )
    print("Connected to the database!")

    # Create a cursor
    cursor = conn.cursor()

    # Fetch all tuples from the USERS table
    cursor.execute("SELECT * FROM USERS;")
    users = cursor.fetchall()

    # Print the tuples
    if users:
        print("Users in the database:")
        for user in users:
            print(user)
    else:
        print("No users found in the database.")

except Exception as e:
    print(f"Error: {e}")

finally:
    # Close the cursor and connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
        print("Database connection closed.")