from flask import Flask, request, jsonify, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

db_config = {
    'dbname': 'postgres',  # Replace with your database name
    'user': 'SENS3011Foxtrot',
    'password': 'your-password',  # Replace with your master password
    'host': 'database-1.ciairzbfckl9.us-east-1.rds.amazonaws.com',
    'port': 5432
}

def get_db_connection():
    conn = psycopg2.connect(**db_config)
    return conn

@app.route('/')
def home():
    return "Hello, Flask!"

# Register
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error: Username/Password required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
        if cur.fetchone():
            return jsonify({'error': 'Username already exists'}), 400

        hashed_password = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s);",
            (username, hashed_password)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()

# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({'message': 'User logging not successful'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
        user = cur.fetchone()

        if not user or not check_password_hash(user[2], password):
            return jsonify({'error': 'Invalid username or password'}), 401

        session['user_id'] = user[0]
        return jsonify({'message': f"User '{username}' logged in successfully."})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()

# Logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None) # Clearing user session
    return jsonify({"message": "Logged out successfully."})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
