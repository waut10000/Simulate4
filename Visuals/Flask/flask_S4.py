from flask import Flask, jsonify, render_template, request
from flask_httpauth import HTTPBasicAuth
import mysql.connector
import json
import bcrypt
import security

app = Flask(__name__, static_folder='templates')
auth = HTTPBasicAuth()

# Load hashed user data
with open('.venv/hashed_users.json', 'r') as f:
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
    return render_template('index.html')

@app.route('/water-level', methods=['GET'])
#@auth.login_required
def water_level():
    meter_info = get_latest_meter_info()
    if meter_info is not None:
        fill_percentage = calculate_fill_percentage(meter_info[0], int(meter_info[1]))
        rounded_fill_percentage = round(fill_percentage)
        return jsonify({'percent': rounded_fill_percentage}), 200
    else:
        return jsonify({'error': 'Meter information not found'}), 404


def get_db_connection():
    conn = mysql.connector.connect(**security.DB_CONFIG)
    return conn

def get_latest_meter_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Adjust the query below according to your actual table names and column names
    query = f'''
    SELECT `Meter-Box`.`Hoogte`, `Meter-Data`.`Diepte` FROM `Meter-Data` 
    INNER JOIN `Meter-Box` ON `Meter-Data`.`Meter-Box-ID` = `Meter-Box`.`ID`
    WHERE `Meter-Box-ID` = '{security.BOX_ID}'
    ORDER BY `Meter-Data`.`Timestamp` DESC Limit 1
    '''
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def calculate_fill_percentage(height, depth):
    # This function needs more details about how capacity and height are related to compute the fill percentage accurately
    filled_height = height - depth
    fill_percentage = (filled_height / height) * 100
    return fill_percentage


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
