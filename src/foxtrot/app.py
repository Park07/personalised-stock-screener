from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model for database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

def create_tables():
    db.create_all()

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

    # If user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        data = request.get_json(force=True)
        username = request.form.get("username")
        password = request.form.get("password")


        if not username or not password:
            return jsonify({'message': 'User loging not successful'}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({'Invalid username or password'}), 401

        session['user_id'] = user.id
        return jsonify({"message": f"User '{username}' logged in successfully."})


# Logout


if __name__ == '__main__':
    app.run(debug=True)

