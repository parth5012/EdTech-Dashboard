from flask import Flask
import os
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv



load_dotenv()


app = Flask(__name__,template_folder='../templates')
app.secret_key = os.getenv('FLASK_API_KEY')

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create it if it doesn’t exist

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



uri = os.getenv("URI")


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,  # Verify connections before using them
    "pool_recycle": 300,  # Recycle connections after 5 minutes
    "connect_args": {"sslmode": "require", "connect_timeout": 10},
}
db.init_app(app)
