from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app, supports_credentials=True)

# MySQL Configuration - XAMPP SETTINGS
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Empty for XAMPP
    'database': 'hospital_db'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database Error: {e}")
        return None

# Initialize Database
def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                user_type ENUM('patient', 'doctor', 'staff', 'admin') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                full_name VARCHAR(200) NOT NULL,
                email VARCHAR(150),
                phone VARCHAR(15),
                date_of_birth DATE,
                gender ENUM('Male', 'Female', 'Other'),
                address TEXT,
                blood_group VARCHAR(5),
                emergency_contact VARCHAR(15),
                insurance_id VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Doctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                full_name VARCHAR(200) NOT NULL,
                email VARCHAR(150),
                phone VARCHAR(15),
                specialization VARCHAR(100),
                qualification VARCHAR(200),
                experience_years INT,
                consultation_fee DECIMAL(10,2),
                department VARCHAR(100),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Staff table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                full_name VARCHAR(200) NOT NULL,
                email VARCHAR(150),
                phone VARCHAR(15),
                position VARCHAR(100),
                department VARCHAR(100),
                salary DECIMAL(10,2),
                shift_timing VARCHAR(50),
                is_available BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Medical Records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT,
                doctor_id INT,
                diagnosis TEXT,
                prescription TEXT,
                treatment_date DATETIME,
                follow_up_date DATE,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
            )
        ''')
        
        # Pharmacy Inventory
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pharmacy (
                id INT AUTO_INCREMENT PRIMARY KEY,
                drug_name VARCHAR(200) NOT NULL,
                category VARCHAR(100),
                manufacturer VARCHAR(200),
                quantity_in_stock INT,
                unit_price DECIMAL(10,2),
                expiry_date DATE,
                description TEXT
            )
        ''')
        
        # Financial Records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finances (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_type ENUM('income', 'expense') NOT NULL,
                amount DECIMAL(12,2),
                category VARCHAR(100),
                description TEXT,
                transaction_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT,
                receiver_id INT,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Insurance Claims
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insurance_claims (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT,
                claim_amount DECIMAL(10,2),
                claim_type VARCHAR(100),
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                submission_date DATE,
                documents TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        
        # Create admin if doesn't exist
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_pass = generate_password_hash('admin123')
            cursor.execute(
                "INSERT INTO users (username, password, user_type) VALUES (%s, %s, %s)",
                ('admin', admin_pass, 'admin')
            )
            conn.commit()
        
        cursor.close()
        conn.close()
        print("✅ Database initialized successfully!")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        user_type = data.get('user_type')
        
        if not username or not password or not user_type:
            return jsonify({'success': False, 'message': 'Missing credentials'})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND user_type = %s",
            (username, user_type)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            
            return jsonify({
                'success': True,
                'user_type': user['user_type'],
                'message': 'Login successful'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/patient_records', methods=['GET'])
def get_patient_records():
    try:
        if 'user_id' not in session or session.get('user_type') != 'patient':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get patient ID
        cursor.execute("SELECT id FROM patients WHERE user_id = %s", (session['user_id'],))
        patient = cursor.fetchone()
        
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'})
        
        # Get medical records
        cursor.execute('''
            SELECT mr.*, d.full_name as doctor_name, d.specialization
            FROM medical_records mr
            JOIN doctors d ON mr.doctor_id = d.id
            WHERE mr.patient_id = %s
            ORDER BY mr.treatment_date DESC
        ''', (patient['id'],))
        
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'records': records})
    except Exception as e:
        print(f"Error fetching records: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/patient_profile', methods=['GET'])
def get_patient_profile():
    try:
        if 'user_id' not in session or session.get('user_type') != 'patient':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM patients WHERE user_id = %s", (session['user_id'],))
        profile = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/doctor_stats', methods=['GET'])
def get_doctor_stats():
    try:
        if 'user_id' not in session or session.get('user_type') != 'doctor':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get doctor ID
        cursor.execute("SELECT id FROM doctors WHERE user_id = %s", (session['user_id'],))
        doctor = cursor.fetchone()
        
        if not doctor:
            return jsonify({'success': False, 'message': 'Doctor not found'})
        
        # Get monthly stats
        cursor.execute('''
            SELECT 
                DATE_FORMAT(treatment_date, '%%Y-%%m') as month,
                COUNT(DISTINCT patient_id) as patient_count
            FROM medical_records
            WHERE doctor_id = %s
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        ''', (doctor['id'],))
        
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/doctor_patients', methods=['GET'])
def get_doctor_patients():
    try:
        if 'user_id' not in session or session.get('user_type') != 'doctor':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id FROM doctors WHERE user_id = %s", (session['user_id'],))
        doctor = cursor.fetchone()
        
        if not doctor:
            return jsonify({'success': False, 'message': 'Doctor not found'})
        
        cursor.execute('''
            SELECT DISTINCT p.*, mr.treatment_date as last_visit
            FROM patients p
            JOIN medical_records mr ON p.id = mr.patient_id
            WHERE mr.doctor_id = %s
            ORDER BY mr.treatment_date DESC
        ''', (doctor['id'],))
        
        patients = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'patients': patients})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/available_nurses', methods=['GET'])
def get_available_nurses():
    try:
        if 'user_id' not in session or session.get('user_type') != 'doctor':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM staff 
            WHERE position LIKE '%%nurse%%' AND is_available = TRUE
        ''')
        
        nurses = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'nurses': nurses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/staff_profile', methods=['GET'])
def get_staff_profile():
    try:
        if 'user_id' not in session or session.get('user_type') != 'staff':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM staff WHERE user_id = %s", (session['user_id'],))
        profile = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin_finances', methods=['GET'])
def get_admin_finances():
    try:
        if 'user_id' not in session or session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                transaction_type,
                SUM(amount) as total
            FROM finances
            GROUP BY transaction_type
        ''')
        summary = cursor.fetchall()
        
        cursor.execute('SELECT full_name, position, salary FROM staff')
        salaries = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'summary': summary, 'salaries': salaries})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/pharmacy', methods=['GET'])
def get_pharmacy():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM pharmacy ORDER BY drug_name")
        inventory = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'inventory': inventory})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.json
        user_message = data.get('message', '')
        language = data.get('language', 'english')
        
        # Simple AI response without Gemini (you can add Gemini later)
        responses = {
            'english': {
                'hello': 'Hello! How can I help you with your healthcare needs today?',
                'appointment': 'To book an appointment, please contact our reception at +91-1234567890 or visit the appointments section.',
                'emergency': 'For emergencies, please call 108 immediately or visit our Emergency Department.',
                'default': 'Thank you for your message. Our healthcare team is here to help. Could you please provide more details?'
            },
            'hindi': {
                'hello': 'नमस्ते! मैं आपकी स्वास्थ्य सेवा में कैसे मदद कर सकता हूं?',
                'appointment': 'अपॉइंटमेंट बुक करने के लिए, कृपया +91-1234567890 पर संपर्क करें।',
                'emergency': 'आपातकाल के लिए, कृपया तुरंत 108 पर कॉल करें।',
                'default': 'आपके संदेश के लिए धन्यवाद। कृपया अधिक विवरण प्रदान करें।'
            },
            'kannada': {
                'hello': 'ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಆರೋಗ್ಯ ಅಗತ್ಯಗಳಿಗೆ ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?',
                'appointment': 'ಅಪಾಯಿಂಟ್ಮೆಂಟ್ ಬುಕ್ ಮಾಡಲು +91-1234567890 ಗೆ ಸಂಪರ್ಕಿಸಿ।',
                'emergency': 'ತುರ್ತು ಪರಿಸ್ಥಿತಿಗಾಗಿ ತಕ್ಷಣ 108 ಗೆ ಕರೆ ಮಾಡಿ।',
                'default': 'ನಿಮ್ಮ ಸಂದೇಶಕ್ಕೆ ಧನ್ಯವಾದಗಳು। ದಯವಿಟ್ಟು ಹೆಚ್ಚಿನ ವಿವರಗಳನ್ನು ನೀಡಿ।'
            }
        }
        
        # Simple keyword matching
        message_lower = user_message.lower()
        lang_responses = responses.get(language, responses['english'])
        
        if 'hello' in message_lower or 'hi' in message_lower or 'hey' in message_lower:
            response = lang_responses['hello']
        elif 'appointment' in message_lower or 'book' in message_lower:
            response = lang_responses['appointment']
        elif 'emergency' in message_lower or 'urgent' in message_lower:
            response = lang_responses['emergency']
        else:
            response = lang_responses['default']
        
        return jsonify({'success': True, 'response': response})
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({'success': False, 'message': 'Sorry, I encountered an error. Please try again.'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000, host='0.0.0.0')