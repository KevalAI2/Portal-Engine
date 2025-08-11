from app.core import app
from app.core.database import create_tables
from app.route import *

# Create database tables on startup
create_tables()
