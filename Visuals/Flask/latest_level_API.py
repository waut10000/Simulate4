from flask import Flask, jsonify
import mysql.connector
from flask_httpauth import HTTPBasicAuth
import json
import bcrypt

app = Flask(__name__)
auth = HTTPBasicAuth()


DB_CONFIG = {
    'user': 'your_db_username',
    'password': 'your_db_password',
    'host': 'localhost',
    'database': 'your_db_name',
    'raise_on_warnings': True
}

# Load hashed user data
with open('hashed_users.json', 'r') as f:
    user_data = json.load(f)

@auth.verify_password
def verify_password(username, password):
    if username in user_data:
        # Compare the provided password with the hashed one
        return bcrypt.checkpw(password.encode('utf-8'), user_data[username].encode('utf-8'))
    return False

@app.route('/')
@auth.login_required
def index():
    return f"Hello, {auth.current_user()}!"

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def get_latest_meter_info():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Adjust the query below according to your actual table names and column names
    query = '''
    SELECT Diepte FROM `Meter-Data` ORDER BY Timestamp DESC Limit 1;
    '''
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def calculate_fill_percentage(depth, height, capacity):
    # This function needs more details about how capacity and height are related to compute the fill percentage accurately
    filled_height = height - depth
    fill_percentage = (filled_height / height) * 100
    return fill_percentage

@app.route('/api/water-level', methods=['GET'])
@auth.login_required
def water_level():
    meter_info = get_latest_meter_info()
    if meter_info is not None:
        fill_percentage = calculate_fill_percentage(meter_info['depth'], meter_info['height'], meter_info['capacity'])
        return jsonify({'percentage': fill_percentage}), 200
    else:
        return jsonify({'error': 'Meter information not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
