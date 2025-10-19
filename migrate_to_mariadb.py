import os
import sys
import subprocess
import pymysql

# Enable PyMySQL to act as MySQLdb (needed if using PyMySQL)
pymysql.install_as_MySQLdb()

# --- CONFIGURE THESE ---
DB_NAME = "payrolldb"
DB_USER = "root"
DB_PASSWORD = "12345678"   # your actual MariaDB password
DB_HOST = "127.0.0.1"
DB_PORT = "7970"           # your custom MariaDB port
# ------------------------

print("🧩 Step 1: Dumping data from old SQLite database...")
subprocess.run([
    "python", "manage.py", "dumpdata",
    "--natural-foreign", "--natural-primary", "--indent", "4", "-o", "full_backup.json"
], check=True)

print("📦 Step 2: Connecting to MariaDB...")

# Try connecting and recreating the database
try:
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=int(DB_PORT))
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Database '{DB_NAME}' created successfully.")
except Exception as e:
    print("❌ Error creating database:", e)
    sys.exit(1)

print("⚙️ Step 3: Updating settings.py to use MariaDB...")

settings_path = os.path.join("payroll", "settings.py")

# Replace DATABASES in settings.py automatically
with open(settings_path, "r", encoding="utf-8") as f:
    content = f.read()

start = content.find("DATABASES =")
end = content.find("AUTH_PASSWORD_VALIDATORS")  # approximate end section marker

if start != -1 and end != -1:
    new_db_config = f"""
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{DB_NAME}',
        'USER': '{DB_USER}',
        'PASSWORD': '{DB_PASSWORD}',
        'HOST': '{DB_HOST}',
        'PORT': '{DB_PORT}',
    }}
}}
"""
    content = content[:start] + new_db_config + content[end:]

    with open(settings_path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Settings updated for MariaDB.")

print("🧱 Step 4: Running migrations...")
subprocess.run(["python", "manage.py", "migrate"], check=True)

print("🚀 Step 5: Loading old data into MariaDB...")
subprocess.run(["python", "manage.py", "loaddata", "full_backup.json"], check=True)

print("🎉 Migration complete! Your data has been imported into MariaDB.")
