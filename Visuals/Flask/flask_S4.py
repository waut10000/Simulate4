from flask import Flask, jsonify, render_template, request, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector
import json
import bcrypt
import security
from mysql.connector import Error

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
@auth.login_required
def water_level():
    try:
        meter_info = get_latest_meter_info()
        if meter_info is not None:
            fill_percentage = calculate_fill_percentage(meter_info[0], int(meter_info[1]))
            rounded_fill_percentage = round(fill_percentage)
            return jsonify({'percent': rounded_fill_percentage}), 200
        else:
            return jsonify({'error': 'Meter information not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/monthly-overview')
@auth.login_required
def monthly_overview():
    return render_template('monthly_overview.html')

@app.route('/monthly-data', methods=['GET'])
def monthly_data():
    try:
        months_only = request.args.get('months_only')
        if months_only:
            months = get_available_months()
            return jsonify({'months': months}), 200
        month = request.args.get('month')
        if month:
            data = get_monthly_data(month)
            if data:
                return jsonify(data), 200
            else:
                abort(404, description="No data found for the selected month")
        else:
            abort(400, description="Month parameter is missing")
    except Exception as e:
        abort(500, description=str(e))

def get_db_connection():
    try:
        conn = mysql.connector.connect(**security.DB_CONFIG)
        return conn
    except Error as e:
        raise Exception(f"Error connecting to database: {str(e)}")

def get_latest_meter_info():
    try:
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
    except Error as e:
        raise Exception(f"Error fetching meter information: {str(e)}")

def calculate_fill_percentage(height, depth):
    # This function needs more details about how capacity and height are related to compute the fill percentage accurately
    filled_height = height - depth
    fill_percentage = (filled_height / height) * 100
    return fill_percentage

def get_available_months():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
        SELECT DISTINCT DATE_FORMAT(`Meter-Data`.`Timestamp`, '%Y-%m') AS month
        FROM `Meter-Data`
        ORDER BY month DESC
        '''
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row[0] for row in result]
    except Exception as e:
        abort(500, description=str(e))

def get_monthly_data(month):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f'''
        SELECT `Meter-Data`.`Timestamp`, `Meter-Box`.`Hoogte`, `Meter-Data`.`Diepte`
        FROM `Meter-Data`
        INNER JOIN `Meter-Box` ON `Meter-Data`.`Meter-Box-ID` = `Meter-Box`.`ID`
        WHERE DATE_FORMAT(`Meter-Data`.`Timestamp`, '%Y-%m') = '{month}'
        ORDER BY `Meter-Data`.`Timestamp` ASC
        '''
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        abort(500, description=str(e))

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error.description)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error.description)}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error.description)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
