
-- Create database
CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('patient','doctor','nurse','admin') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    dob DATE,
    gender VARCHAR(10),
    phone VARCHAR(20),
    address VARCHAR(255),
    insurance_provider VARCHAR(100),
    insurance_id VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Doctors table
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    designation VARCHAR(100),
    qualification VARCHAR(100),
    specialization VARCHAR(100),
    years_experience INT,
    phone VARCHAR(20),
    email VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Nurses table
CREATE TABLE IF NOT EXISTS nurses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_available TINYINT(1) DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Medical records
CREATE TABLE IF NOT EXISTS medical_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    visit_date DATE NOT NULL,
    diagnosis TEXT,
    treatment TEXT,
    prescription TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- Bills
CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_mode ENUM('cash','card','insurance') NOT NULL,
    insurance_claimed TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Messages for patient-doctor chat
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    sender_user_id INT NOT NULL,
    receiver_user_id INT NOT NULL,
    content TEXT NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    FOREIGN KEY (sender_user_id) REFERENCES users(id),
    FOREIGN KEY (receiver_user_id) REFERENCES users(id)
);

-- Nurse calls
CREATE TABLE IF NOT EXISTS nurse_calls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT NOT NULL,
    nurse_id INT NULL,
    status ENUM('pending','accepted','completed') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    FOREIGN KEY (nurse_id) REFERENCES nurses(id)
);

-- Pharmacy inventory
CREATE TABLE IF NOT EXISTS pharmacy_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drug_name VARCHAR(100) NOT NULL,
    units_available INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

-- Salaries
CREATE TABLE IF NOT EXISTS salaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month_year VARCHAR(7) NOT NULL, -- e.g. 2025-12
    amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Insert sample users
INSERT INTO users (username, password_hash, role) VALUES
('patient1', 'scrypt:32768:8:1$XdkBUIPJHksHLTKk$014c8d322c6504622195514371457b23b0b8722525c2b38dd6c0a859ff873bb9a856e582485005639181fb4e5af3a692483d04d44f0250128e7533c8880b8a59', 'patient'),
('patient2', 'scrypt:32768:8:1$S7DdyfzdjqZMcm52$5ef27067eafdcefbe334e3f8d7824ba198586035e7762fed227c4e3715d8f2630a019a25f99cf7caf6d9be41bfb2cf140ebde09d1ddf8927518d06f4058b9c5d', 'patient'),
('patient3', 'scrypt:32768:8:1$bBS1ySRPci0lVjLl$23dd3943bb90ad77efe11c5f6f9a7749945f4069d8a3e18eea6c85212dd8794a6e5fac69aa784f96801cbc462765856152e63234793475a08aeea47bbb57d93f', 'patient'),
('doctor1', 'scrypt:32768:8:1$361vm7kexSSjQNrl$0c725c4ef96229ff9081844cf5b02a36b464e49e3c2123224918ce0584b13e4b5e34996ddf59cf034be746f344aa5f366739a06b4b9e3961e2fe6b6f69a9f136', 'doctor'),
('doctor2', 'scrypt:32768:8:1$4cxKcSRe5y9QNuUF$2440edaf96e3e6b9b02c5513ec21f9ade1d7ce18111beeebb91f5bf27b7b07daaba47f1f09d8f10751a47f6a3242a454156dfa784294e6e3181acf486e35079b', 'doctor'),
('doctor3', 'scrypt:32768:8:1$JFabEi9k4XCyRzsH$93ec034f4aaab36c53f913087bb6bd52bb3fe0532ca32fbead0f5ab873dae9428204da7cead70b746e5a90f3d5262a8be82a4cdb79251adeebca97c460444d25', 'doctor'),
('nurse1', 'scrypt:32768:8:1$AkveXCKOW4mc5nC8$a617d844da4428637cef7df8b4c9039a429a9ba7cd20cfbe79cf69e33581135da39aed46092e06f8e235b1acc6b702d7b7c1c5fad1e8a3a7897770cfb51261ac', 'nurse'),
('nurse2', 'scrypt:32768:8:1$od1AsdYGzJbwAw86$691aa219546e175caa371a5ea1a79c2d029d38dffbce3fb7d940f6474e91a267fef695a076a90ae89dc39a12e19268476e1cb4c4939a40d1d4e453687bf101ac', 'nurse'),
('nurse3', 'scrypt:32768:8:1$U4OcpsSuMBJ2o9Cl$8ab19d5a6284db28a9b1c02d0c5615c377c36122dad2927fffa4e84b574521fcc3cc96f4ce50f620dc7d8be92bd8a053a0b5c6981984c4c4f88dcde710008b51', 'nurse'),
('admin1', 'scrypt:32768:8:1$Z7LJOnESoXNBlI9e$af24dea6016fd775a837716a950fcbfc04178645c437bcf622d5af463115717894575c34fd2a4bc44a3a95b1890f745baaa0136ec6896a77a3466f260388d7a2', 'admin'),
('admin2', 'scrypt:32768:8:1$DicngBIAHLiMRuRv$9a2d9e83ba44a6675c98e8f95ae1cfac1765f8b90722449a0b6d5b629f399f8e235aa674a55ff0ee45e98e2afb795eae6acfc1d05e6ad8153a746f980195cf20', 'admin'),
('admin3', 'scrypt:32768:8:1$QxOtfYbHVpToL1Nt$7b1cb2cb44ca2b2639c6b74aa7c4de3483c7b2caaf8ff9a2777051f72775feaba56f281b942808733ab91ad8061118b976758f6ee96c71d2a2358b521e84a48c', 'admin');

-- Sample patients (linked to first 3 patient users: ids 1,2,3)
INSERT INTO patients (user_id, full_name, dob, gender, phone, address, insurance_provider, insurance_id) VALUES
(1, 'Rahul Sharma', '1990-05-12', 'Male', '9876543210', 'Bangalore, India', 'MediCare Plus', 'MC12345'),
(2, 'Anita Desai', '1985-09-21', 'Female', '9876501234', 'Mumbai, India', 'HealthSecure', 'HS54321'),
(3, 'Vikram Singh', '1978-02-03', 'Male', '9988776655', 'Delhi, India', 'LifeGuard', 'LG11223');

-- Sample doctors (user ids 4,5,6)
INSERT INTO doctors (user_id, full_name, designation, qualification, specialization, years_experience, phone, email) VALUES
(4, 'Dr. Arjun Mehta', 'Consultant', 'MBBS, MD', 'Cardiology', 10, '9000000001', 'arjun.mehta@hospital.com'),
(5, 'Dr. Priya Nair', 'Senior Consultant', 'MBBS, MS', 'Orthopedics', 12, '9000000002', 'priya.nair@hospital.com'),
(6, 'Dr. Karan Malhotra', 'Junior Consultant', 'MBBS', 'General Medicine', 5, '9000000003', 'karan.malhotra@hospital.com');

-- Sample nurses (user ids 7,8,9)
INSERT INTO nurses (user_id, full_name, department, phone, email, is_available) VALUES
(7, 'Nurse Sita Rao', 'ICU', '9111111111', 'sita.rao@hospital.com', 1),
(8, 'Nurse Geeta Pillai', 'Emergency', '9222222222', 'geeta.pillai@hospital.com', 1),
(9, 'Nurse Mohan Das', 'Ward', '9333333333', 'mohan.das@hospital.com', 0);

-- Sample admins (user ids 10,11,12)
INSERT INTO admins (user_id, full_name, phone, email) VALUES
(10, 'Ravi Kumar', '9444444444', 'ravi.kumar@hospital.com'),
(11, 'Sunita Verma', '9555555555', 'sunita.verma@hospital.com'),
(12, 'Mahesh Gupta', '9666666666', 'mahesh.gupta@hospital.com');

-- Sample medical records
INSERT INTO medical_records (patient_id, doctor_id, visit_date, diagnosis, treatment, prescription) VALUES
(1, 1, '2025-11-01', 'Hypertension', 'Lifestyle changes and medication', 'Tab Amlodipine 5mg OD'),
(1, 3, '2025-11-20', 'Fever and cough', 'Symptomatic treatment', 'Tab Paracetamol 650mg TID'),
(2, 2, '2025-10-15', 'Knee pain', 'Physiotherapy and pain relief', 'Tab Ibuprofen 400mg BD'),
(3, 1, '2025-09-10', 'Chest discomfort', 'ECG and observation', 'Tab Aspirin 75mg OD');

-- Sample bills
INSERT INTO bills (patient_id, total_amount, payment_mode, insurance_claimed, created_at) VALUES
(1, 5000.00, 'card', 0, '2025-11-01 10:30:00'),
(1, 1500.00, 'cash', 0, '2025-11-20 12:45:00'),
(2, 12000.00, 'insurance', 1, '2025-10-15 09:15:00'),
(3, 8000.00, 'insurance', 1, '2025-09-10 14:20:00');

-- Sample messages between patient1 and doctor1
INSERT INTO messages (patient_id, doctor_id, sender_user_id, receiver_user_id, content, sent_at) VALUES
(1, 1, 1, 4, 'Doctor, I have been feeling dizzy lately.', '2025-11-25 09:00:00'),
(1, 1, 4, 1, 'Please make sure you are hydrated and monitor your blood pressure.', '2025-11-25 09:10:00'),
(1, 1, 1, 4, 'Okay doctor, I will do that. Thank you!', '2025-11-25 09:15:00');

-- Sample nurse calls
INSERT INTO nurse_calls (doctor_id, nurse_id, status, created_at) VALUES
(1, 1, 'accepted', '2025-11-01 11:00:00'),
(1, NULL, 'pending', '2025-11-02 10:00:00'),
(2, 2, 'completed', '2025-10-15 16:00:00');

-- Sample pharmacy inventory
INSERT INTO pharmacy_inventory (drug_name, units_available, unit_price) VALUES
('Paracetamol 650mg', 200, 2.50),
('Amlodipine 5mg', 150, 5.00),
('Ibuprofen 400mg', 180, 3.00);

-- Sample salaries
INSERT INTO salaries (user_id, month_year, amount) VALUES
(4, '2025-11', 150000.00),
(5, '2025-11', 180000.00),
(6, '2025-11', 120000.00),
(7, '2025-11', 60000.00),
(8, '2025-11', 62000.00),
(9, '2025-11', 58000.00),
(10, '2025-11', 90000.00),
(11, '2025-11', 95000.00),
(12, '2025-11', 88000.00);
