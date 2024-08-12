# models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    contact_number = db.Column(db.String(15), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    accepted = db.Column(db.Boolean, default=False)  # New field for acceptance status
    otp = db.Column(db.String(6))  # For OTP
    otp_expiry = db.Column(db.DateTime)  # For OTP expiry
    def __repr__(self):
        return f'<User {self.username}>'
