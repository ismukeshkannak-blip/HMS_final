import os

# MySQL configuration - adjust according to your XAMPP setup
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # put your MySQL/XAMPP password here if you set one
    "database": "db_init",   # ← use the database you just created
    "port": 3306,
}


# Flask secret key
SECRET_KEY = "change-this-secret-key"

# Gemini / Google Generative AI API key
# Set this in your environment before running:
#   set GEMINI_API_KEY=your_key_here   (Windows)
#   export GEMINI_API_KEY=your_key_here (macOS / Linux)
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
