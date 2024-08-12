# app.py
from flask import Flask, render_template, request
from user import user_bp
from admin import admin_bp  # Import admin blueprint
from models import db
import os
from pyngrok import ngrok
ngrok.set_auth_token('2j6yZx3KvVeSEOhGHG0bEjNdWB8_2ri6c36iDuZZxMJxxCD47')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'S1t2a3r4'  # Replace with your secret key

# Initialize the database
db.init_app(app)
def add_cache_control(response):
    if request.endpoint in ['admin.admin_dashboard', 'admin.logout']:
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response
# Register blueprints
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)  # Register admin blueprint

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Ensure the database tables are created

    with app.app_context():
        db.create_all()
    public_url = ngrok.connect(5000)
    print("Public URL:", public_url)
    app.run()
    #app.run(debug=True)
