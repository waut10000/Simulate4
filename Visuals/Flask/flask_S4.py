from flask import Flask, jsonify, render_template, request, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector
import json
import bcrypt
import security
from mysql.connector import Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

app = Flask(__name__, static_folder='templates')
auth = HTTPBasicAuth()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load hashed user data
try:
    with open('.venv/hashed_users.json', 'r') as f:
        user_data = json.load(f)
except Exception as e:
    logging.error(f"Error loading user data: {str(e)}")
    user_data = {}

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
        box_id = request.args.get('box_id')
        if not box_id:
            return jsonify({'error': 'Box ID is required'}), 400

        meter_info = get_latest_meter_info(box_id)
        if meter_info is not None:
            fill_percentage = calculate_fill_percentage(meter_info[0], float(meter_info[1]))
            rounded_fill_percentage = round(fill_percentage)
            if rounded_fill_percentage <= 20:
                EMAIL_SUBJECT = 'Kritiek regenwaterput niveau '
                send_email_notification(
                    EMAIL_SUBJECT,
                    f'''Waarschuwing: Het niveau van uw regenwaterput is {rounded_fill_percentage}%!
                        Aangeraden uw regenwaterput bij te vullen.'''
                )
            return jsonify({'percent': rounded_fill_percentage}), 200
        else:
            return jsonify({'error': 'Meter information not found'}), 404
    except Exception as e:
        logging.error(f"Error in /water-level: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/monthly-overview')
@auth.login_required
def monthly_overview():
    return render_template('monthly_overview.html')

@app.route('/monthly-data', methods=['GET'])
def monthly_data():
    try:
        months_only = request.args.get('months_only')
        box_id = request.args.get('box_id')
        if not box_id:
            abort(400, description="Box ID is required")

        if months_only:
            months = get_available_months(box_id)
            return jsonify({'months': months}), 200

        month = request.args.get('month')
        if month:
            data = get_monthly_data(month, box_id)
            if data:
                return jsonify(data), 200
            else:
                abort(404, description="No data found for the selected month")
        else:
            abort(400, description="Month parameter is missing")
    except Exception as e:
        logging.error(f"Error in /monthly-data: {str(e)}")
        abort(500, description=str(e))

@app.route('/user-boxes', methods=['GET'])
@auth.login_required
def user_boxes():
    try:
        username = auth.current_user()
        boxes = get_user_boxes(username)
        return jsonify({'boxes': boxes}), 200
    except Exception as e:
        logging.error(f"Error in /user-boxes: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_db_connection():
    try:
        conn = mysql.connector.connect(**security.DB_CONFIG)
        return conn
    except Error as e:
        logging.error(f"Error connecting to database: {str(e)}")
        raise Exception(f"Error connecting to database: {str(e)}")

def get_latest_meter_info(box_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f'''
        SELECT `Meter-Box`.`Hoogte`, `Meter-Data`.`Diepte` 
        FROM `Meter-Data` 
        INNER JOIN `Meter-Box` ON `Meter-Data`.`Meter-Box-ID` = `Meter-Box`.`ID`
        WHERE `Meter-Box-ID` = %s
        ORDER BY `Meter-Data`.`Timestamp` DESC Limit 1
        '''
        cursor.execute(query, (box_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    except Error as e:
        logging.error(f"Error fetching meter information: {str(e)}")
        raise Exception(f"Error fetching meter information: {str(e)}")

def calculate_fill_percentage(height, depth):
    filled_height = height - depth
    fill_percentage = (filled_height / height) * 100
    return fill_percentage

def get_available_months(box_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
        SELECT DISTINCT DATE_FORMAT(`Meter-Data`.`Timestamp`, '%Y-%m') AS month
        FROM `Meter-Data`
        WHERE `Meter-Box-ID` = %s
        ORDER BY month DESC
        '''
        cursor.execute(query, (box_id,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row[0] for row in result]
    except Error as e:
        logging.error(f"Error fetching available months: {str(e)}")
        abort(500, description=str(e))

def get_monthly_data(month, box_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f'''
        SELECT `Meter-Data`.`Timestamp`, `Meter-Box`.`Hoogte`, `Meter-Data`.`Diepte`
        FROM `Meter-Data`
        INNER JOIN `Meter-Box` ON `Meter-Data`.`Meter-Box-ID` = `Meter-Box`.`ID`
        WHERE DATE_FORMAT(`Meter-Data`.`Timestamp`, '%Y-%m') = %s AND `Meter-Box-ID` = %s
        ORDER BY `Meter-Data`.`Timestamp` ASC
        '''
        cursor.execute(query, (month, box_id))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Error as e:
        logging.error(f"Error fetching monthly data: {str(e)}")
        abort(500, description=str(e))

def get_user_boxes(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
        SELECT `Box-ID`, `Meter-Box`.`Location`
        FROM `User-Box`
        INNER JOIN `Meter-Box` ON `User-Box`.`Box-ID` = `Meter-Box`.`ID`
        INNER JOIN `User` ON `User-Box`.`User-ID` = `User`.`idUser`
        WHERE `User`.`User` = %s
        '''
        cursor.execute(query, (username,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return [{'id': row[0], 'name': row[1]} for row in result]
    except Error as e:
        logging.error(f"Error fetching user boxes: {str(e)}")
        raise Exception(f"Error fetching user boxes: {str(e)}")

def send_email_notification(subject, body):
    msg = MIMEMultipart()
    msg['From'] = security.EMAIL_FROM
    msg['To'] = security.EMAIL_TO
    msg['Subject'] = subject
    msg['X-Priority'] = '1'  # Mark as high priority
    msg['X-MSMail-Priority'] = 'High'  # Mark as high priority for MS Outlook
    msg['Importance'] = 'High'  # Mark as high priority for MS Outlook

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(security.SMTP_SERVER, security.SMTP_PORT) as server:
            server.starttls()
            server.login(security.SMTP_USERNAME, security.SMTP_PASSWORD)
            server.sendmail(security.EMAIL_FROM, security.EMAIL_TO, msg.as_string())
        print('Email sent successfully.')
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")

@app.route("/privacy")
def privacy():
    return '', 200

@app.route("/terms")
def terms():
    return '', 200

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
