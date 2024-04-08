from flask import Flask, jsonify
import mysql.connector
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "admin": "admmin",  # You should replace this with your desired username and password
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

DB_CONFIG = {
    'user': 'your_db_username',
    'password': 'your_db_password',
    'host': 'localhost',
    'database': 'your_db_name',
    'raise_on_warnings': True
}

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def get_latest_water_level():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT level FROM water_levels ORDER BY timestamp DESC LIMIT 1')
    water_level = cursor.fetchone()
    cursor.close()
    conn.close()
    if water_level:
        return water_level['level']
    else:
        return None

@app.route('/api/water-level', methods=['GET'])
@auth.login_required
def water_level():
    level = get_latest_water_level()
    if level is not None:
        return jsonify({'percentage': level}), 200
    else:
        return jsonify({'error': 'Water level data not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # Listen on all available IPs
