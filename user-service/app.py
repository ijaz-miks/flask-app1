import os
import mysql.connector
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Database configuration from environment variables
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "3306")  # Default MySQL port
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except mysql.connector.Error as error:
        print("Error connecting to database:", error)
    return conn

# Create users table if it doesn't exist
def create_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE
            )
        ''')
        conn.commit()
        cursor.close()
    except mysql.connector.Error as error:
        print("Error creating table:", error)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()

create_table()

@app.route('/users', methods=['POST'])
def create_user():
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor()
        data = request.json
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({'message': 'Bad Request: name and email are required'}), 400
        try:
            cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (data['name'], data['email']))
            conn.commit()
            user_id = cursor.lastrowid
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            user_data = {
                'id': user[0],
                'name': user[1],
                'email': user[2]
            }
            return jsonify({'message': 'User created successfully', 'user': user_data}), 201
        except mysql.connector.Error as error:
            print("Error creating user:", error)
            conn.rollback()
            return jsonify({'message': 'Failed to create user'}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'message': 'Database connection failed'}), 500

@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        user_list = [{'id': user[0], 'name': user[1], 'email': user[2]} for user in users]
        return jsonify({'users': user_list})
    else:
        return jsonify({'message': 'Database connection failed'}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            user_data = {'id': user[0], 'name': user[1], 'email': user[2]}
            return jsonify({'user': user_data})
        return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'Database connection failed'}), 500

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor()
        data = request.json
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                if not data:
                    return jsonify({'message': 'Bad Request: No data provided for update'}), 400
                if 'name' in data:
                    cursor.execute("UPDATE users SET name = %s WHERE id = %s", (data['name'], user_id))
                if 'email' in data:
                    cursor.execute("UPDATE users SET email = %s WHERE id = %s", (data['email'], user_id))
                conn.commit()
                return jsonify({'message': 'User updated successfully'})
            return jsonify({'message': 'User not found'}), 404
        except mysql.connector.Error as error:
            print("Error updating user:", error)
            conn.rollback()
            return jsonify({'message': 'Failed to update user'}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'message': 'Database connection failed'}), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                return jsonify({'message': 'User deleted successfully'})
            return jsonify({'message': 'User not found'}), 404
        except mysql.connector.Error as error:
            print("Error deleting user:", error)
            conn.rollback()
            return jsonify({'message': 'Failed to delete user'}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'message': 'Database connection failed'}), 500

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)