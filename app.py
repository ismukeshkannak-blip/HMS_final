from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
import mysql.connector
from mysql.connector import Error
from functools import wraps
import os

import google.generativeai as genai

from config import MYSQL_CONFIG, SECRET_KEY, GEMINI_API_KEY_ENV

app = Flask(__name__)
app.secret_key = SECRET_KEY


def get_db():
    return mysql.connector.connect(**MYSQL_CONFIG)


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND role=%s", (username, role))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
        except Error as e:
            error = f'Database error: {e}'
            user = None

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            if role == 'patient':
                return redirect(url_for('patient_dashboard'))
            if role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            if role == 'nurse':
                return redirect(url_for('nurse_dashboard'))
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            if not error:
                error = 'Invalid credentials'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# -------------------- Patient portal --------------------


@app.route('/patient')
@login_required('patient')
def patient_dashboard():
    tab = request.args.get('tab', 'profile')
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE user_id=%s", (user_id,))
    patient = cursor.fetchone()

    context = {'active_tab': tab, 'patient': patient}

    if tab == 'records':
        cursor.execute(
            "SELECT mr.*, d.full_name AS doctor_name "
            "FROM medical_records mr "
            "JOIN doctors d ON mr.doctor_id = d.id "
            "WHERE mr.patient_id = %s "
            "ORDER BY mr.visit_date DESC",
            (patient['id'],)
        )
        context['records'] = cursor.fetchall()

    elif tab == 'billing':
        cursor.execute(
            "SELECT * FROM bills WHERE patient_id=%s ORDER BY created_at DESC",
            (patient['id'],)
        )
        context['bills'] = cursor.fetchall()

    elif tab == 'chat':
        cursor.execute(
            "SELECT mr.doctor_id, d.full_name, d.specialization "
            "FROM medical_records mr "
            "JOIN doctors d ON mr.doctor_id = d.id "
            "WHERE mr.patient_id=%s "
            "ORDER BY mr.visit_date DESC "
            "LIMIT 1",
            (patient['id'],)
        )
        doctor = cursor.fetchone()
        context['doctor'] = doctor
        if doctor:
            cursor.execute(
                "SELECT * FROM messages "
                "WHERE patient_id=%s AND doctor_id=%s "
                "ORDER BY sent_at ASC",
                (patient['id'], doctor['doctor_id'])
            )
            context['messages'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('patient_dashboard.html', **context)


@app.route('/patient/chat/send', methods=['POST'])
@login_required('patient')
def patient_send_message():
    content = request.form['content'].strip()
    if not content:
        return redirect(url_for('patient_dashboard', tab='chat'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE user_id=%s", (session['user_id'],))
    patient = cursor.fetchone()

    cursor.execute(
        "SELECT mr.doctor_id "
        "FROM medical_records mr "
        "WHERE mr.patient_id=%s "
        "ORDER BY mr.visit_date DESC "
        "LIMIT 1",
        (patient['id'],)
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return redirect(url_for('patient_dashboard', tab='chat'))

    doctor_id = row['doctor_id']

    cursor.execute("SELECT user_id FROM doctors WHERE id=%s", (doctor_id,))
    dr = cursor.fetchone()
    cursor.execute("SELECT id FROM users WHERE id=%s", (dr['user_id'],))
    doctor_user = cursor.fetchone()

    cursor.execute(
        "INSERT INTO messages (patient_id, doctor_id, sender_user_id, receiver_user_id, content) "
        "VALUES (%s,%s,%s,%s,%s)",
        (patient['id'], doctor_id, session['user_id'], doctor_user['id'], content)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('patient_dashboard', tab='chat'))


@app.route('/api/patient-assistant', methods=['POST'])
@login_required('patient')
def patient_assistant_api():
    data = request.get_json(force=True)
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    api_key = os.getenv(GEMINI_API_KEY_ENV)
    if not api_key:
        return jsonify({'error': 'Gemini API key not configured on server.'}), 500

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = (
            "You are a virtual assistant for a hospital patient portal. "
            "You can answer general medical and hospital-process questions in simple language, "
            "but you must not provide definitive diagnoses, prescribe medicine, or override doctors. "
            "Always encourage patients to consult their doctor for serious or urgent issues.\n\n"
            f"Patient question: {message}"
        )
        response = model.generate_content(prompt)
        reply_text = response.text.strip() if response and response.text else "I'm sorry, I couldn't generate a response."
        return jsonify({'reply': reply_text})
    except Exception as e:
        return jsonify({'error': f'Assistant error: {e}'}), 500


# -------------------- Doctor portal --------------------


@app.route('/doctor')
@login_required('doctor')
def doctor_dashboard():
    tab = request.args.get('tab', 'profile')
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM doctors WHERE user_id=%s", (user_id,))
    doctor = cursor.fetchone()

    context = {'active_tab': tab, 'doctor': doctor}

    if tab == 'stats':
        cursor.execute(
            "SELECT DATE_FORMAT(visit_date, '%%Y-%%m') AS month_year, "
            "COUNT(*) AS patient_count "
            "FROM medical_records "
            "WHERE doctor_id=%s "
            "GROUP BY month_year "
            "ORDER BY month_year DESC",
            (doctor['id'],)
        )
        stats = cursor.fetchall()
        context['stats_by_month'] = stats
        selected_month = request.args.get('month') or (stats[0]['month_year'] if stats else None)
        context['selected_month'] = selected_month
        context['selected_stats'] = None
        if selected_month:
            for row in stats:
                if row['month_year'] == selected_month:
                    context['selected_stats'] = row
                    break

    elif tab == 'chat':
        cursor.execute(
            "SELECT DISTINCT p.* "
            "FROM medical_records mr "
            "JOIN patients p ON mr.patient_id = p.id "
            "WHERE mr.doctor_id=%s",
            (doctor['id'],)
        )
        patients = cursor.fetchall()
        context['patients'] = patients

        patient_id = request.args.get('patient_id', type=int)
        if patient_id:
            cursor.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
            context['selected_patient'] = cursor.fetchone()
            cursor.execute(
                "SELECT * FROM messages "
                "WHERE patient_id=%s AND doctor_id=%s "
                "ORDER BY sent_at ASC",
                (patient_id, doctor['id'])
            )
            context['messages'] = cursor.fetchall()

    elif tab == 'nurses':
        cursor.execute("SELECT * FROM nurses ORDER BY full_name")
        context['nurses'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('doctor_dashboard.html', **context)


@app.route('/doctor/chat/send/<int:patient_id>', methods=['POST'])
@login_required('doctor')
def doctor_send_message(patient_id):
    content = request.form['content'].strip()
    if not content:
        return redirect(url_for('doctor_dashboard', tab='chat', patient_id=patient_id))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM doctors WHERE user_id=%s", (session['user_id'],))
    doctor = cursor.fetchone()

    cursor.execute(
        "SELECT u.id FROM patients p JOIN users u ON p.user_id=u.id WHERE p.id=%s",
        (patient_id,)
    )
    patient_user = cursor.fetchone()

    cursor.execute(
        "INSERT INTO messages (patient_id, doctor_id, sender_user_id, receiver_user_id, content) "
        "VALUES (%s,%s,%s,%s,%s)",
        (patient_id, doctor['id'], session['user_id'], patient_user['id'], content)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('doctor_dashboard', tab='chat', patient_id=patient_id))


@app.route('/doctor/call-nurse/<int:nurse_id>', methods=['POST'])
@login_required('doctor')
def doctor_call_nurse(nurse_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM doctors WHERE user_id=%s", (session['user_id'],))
    doctor = cursor.fetchone()
    cursor.execute(
        "INSERT INTO nurse_calls (doctor_id, nurse_id, status) VALUES (%s,%s,'pending')",
        (doctor['id'], nurse_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('doctor_dashboard', tab='nurses'))


# -------------------- Nurse portal --------------------


@app.route('/nurse')
@login_required('nurse')
def nurse_dashboard():
    tab = request.args.get('tab', 'profile')
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM nurses WHERE user_id=%s", (user_id,))
    nurse = cursor.fetchone()

    context = {'active_tab': tab, 'nurse': nurse}

    if tab == 'notifications':
        cursor.execute(
            "SELECT nc.*, d.full_name AS doctor_name "
            "FROM nurse_calls nc "
            "JOIN doctors d ON nc.doctor_id = d.id "
            "WHERE (nc.nurse_id IS NULL OR nc.nurse_id=%s) "
            "ORDER BY nc.created_at DESC",
            (nurse['id'],)
        )
        context['calls'] = cursor.fetchall()

    elif tab == 'inventory':
        cursor.execute("SELECT * FROM pharmacy_inventory ORDER BY drug_name")
        context['inventory'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('nurse_dashboard.html', **context)


@app.route('/nurse/accept-call/<int:call_id>', methods=['POST'])
@login_required('nurse')
def nurse_accept_call(call_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM nurses WHERE user_id=%s", (session['user_id'],))
    nurse = cursor.fetchone()
    cursor.execute(
        "UPDATE nurse_calls SET nurse_id=%s, status='accepted' WHERE id=%s",
        (nurse['id'], call_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('nurse_dashboard', tab='notifications'))


# -------------------- Admin portal --------------------


@app.route('/admin')
@login_required('admin')
def admin_dashboard():
    tab = request.args.get('tab', 'finances')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    context = {'active_tab': tab}

    if tab == 'finances':
        cursor.execute(
            "SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS month_year, "
            "SUM(total_amount) AS total_revenue "
            "FROM bills "
            "GROUP BY month_year "
            "ORDER BY month_year DESC"
        )
        context['revenue_by_month'] = cursor.fetchall()

        cursor.execute(
            "SELECT b.*, p.full_name AS patient_name "
            "FROM bills b "
            "JOIN patients p ON b.patient_id=p.id "
            "ORDER BY b.created_at DESC"
        )
        context['bills'] = cursor.fetchall()

    elif tab == 'inventory':
        cursor.execute("SELECT * FROM pharmacy_inventory ORDER BY drug_name")
        context['inventory'] = cursor.fetchall()

    elif tab == 'salaries':
        cursor.execute(
            "SELECT s.*, u.role, "
            "COALESCE(p.full_name, d.full_name, n.full_name, a.full_name) AS full_name "
            "FROM salaries s "
            "JOIN users u ON s.user_id = u.id "
            "LEFT JOIN patients p ON p.user_id = u.id "
            "LEFT JOIN doctors d ON d.user_id = u.id "
            "LEFT JOIN nurses n ON n.user_id = u.id "
            "LEFT JOIN admins a ON a.user_id = u.id "
            "ORDER BY s.month_year DESC, full_name"
        )
        context['salaries'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', **context)


if __name__ == '__main__':
    app.run(debug=True)
