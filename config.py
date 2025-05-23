import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', 'oci.jmcloudpro.com')
MYSQL_USER = os.getenv('MYSQL_USER', 'admin')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'admin')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'salvecoin')

# Database connection string
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
