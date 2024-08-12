from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import random
import datetime
import os
from video_detection import process_video, create_directories, load_models, initialize


user_bp = Blueprint('user', __name__)




@user_bp.route('/user/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        contact_number = request.form.get('contact_number')
        dob_str = request.form.get('dob')  # Date as string from form
        password = request.form.get('password')

        # Basic validation
        errors = []
        
        if not username or not email or not contact_number or not dob_str or not password or not name:
            errors.append('Please fill out all fields')

        if not username.islower() or ' ' in username or len(username) > 20:
            errors.append('Username must contain only lowercase letters and numbers, and be up to 20 characters long')

        if len(name) > 50:
            errors.append('Name must be within 50 characters')

        if len(email) > 50:
            errors.append('Email must be within 50 characters')

        if len(contact_number) > 15:
            errors.append('Contact number must be within 15 characters')

        if len(password) > 20:
            errors.append('Password must be within 20 characters')

        # Convert the date string to a Python date object
        try:
            dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
            if dob > datetime.date.today():
                errors.append('Date of birth cannot be in the future')
        except ValueError:
            errors.append('Invalid date format. Use YYYY-MM-DD.')

        # Check if username, email, or contact number already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username is already taken')

        if User.query.filter_by(email=email).first():
            errors.append('Email is already registered')

        if User.query.filter_by(contact_number=contact_number).first():
            errors.append('Contact number is already registered')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('user.signup'))

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create a new user
        new_user = User(
            username=username, email=email, contact_number=contact_number,
            name=name, dob=dob, password=hashed_password
        )

        # Add to database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('user.wait_for_verification'))

    return render_template('user_signup.html')

@user_bp.route('/user/wait_for_verification')
def wait_for_verification():
    return render_template('wait_for_verification.html')

@user_bp.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')  # This will be username, email, or contact number
        password = request.form.get('password')
        
        user = User.query.filter(
            (User.username == identifier) |
            (User.email == identifier) |
            (User.contact_number == identifier)
        ).first()

        if user:
            if user.accepted:
                if check_password_hash(user.password, password):
                    session['user_id'] = user.id
                    return redirect(url_for('user.home'))
                else:
                    flash('Incorrect password.', 'danger')
            else:
                flash('Account not verified by admin. Please ask the admin for verification.', 'warning')
        else:
            flash('Incorrect user ID.', 'danger')

    return render_template('user_login.html')

# Home Route
@user_bp.route('/user/home')
def home():
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('user.login'))
    return render_template('home.html')

@user_bp.route('/user/video_detection')
def video_detection():
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('user.login'))
    return render_template('video_detection.html')


@user_bp.route('/user/upload', methods=['POST'])
def upload_file():
    # Initialize the directories, models, and configurations
    UPLOAD_FOLDER, PROCESSED_FOLDER, LRCN_model, yolo_model, object_list, IMAGE_HEIGHT, IMAGE_WIDTH, SEQUENCE_LENGTH, CLASSES_LIST = initialize()

    # Set configurations for Flask app
    app = current_app
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

    if 'videoFile' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['videoFile']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    if file:
        try:
            input_video_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_video_path)
            
            output_video_path = os.path.join(app.config['PROCESSED_FOLDER'], 'processed_' + file.filename)
            
            # Process the video with all required arguments
            process_video(input_video_path, output_video_path, LRCN_model, yolo_model, object_list, IMAGE_HEIGHT, IMAGE_WIDTH, SEQUENCE_LENGTH, CLASSES_LIST)
            
            return jsonify({'success': True, 'download_url': url_for('user.download_file', filename='processed_' + file.filename)})
        except Exception as e:
            print(f"Error during processing: {e}")
            return jsonify({'success': False, 'message': str(e)})

@user_bp.route('/user/download/<filename>', methods=['GET'])
def download_file(filename):
    app = current_app
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

# Live Video Route
@user_bp.route('/user/live_video')
def live_video():
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('user.login'))
    return render_template('live_video.html')

@user_bp.route('/user/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('user.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name')
        contact_number = request.form.get('contact_number')
        dob_str = request.form.get('dob')

        errors = []

        if not name or not contact_number or not dob_str:
            errors.append('Please fill out all fields')

        if len(name) > 50:
            errors.append('Name must be within 50 characters')

        if len(contact_number) > 15:
            errors.append('Contact number must be within 15 characters')

        try:
            dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
            if dob > datetime.date.today():
                errors.append('Date of birth cannot be in the future')
        except ValueError:
            errors.append('Invalid date format. Use YYYY-MM-DD.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('user.profile'))

        user.name = name
        user.contact_number = contact_number
        user.dob = dob
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile'))

    return render_template('profile.html', user=user)
@user_bp.route('/user/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'info')
    return redirect(url_for('user.login'))  # Redirect to login page



@user_bp.route('/user/forget_password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        user_id = request.form.get('user_id')  # This could be username, email, or contact number
        
        # Query the user by username, email, or contact number
        user = User.query.filter(
            (User.username == user_id) |
            (User.email == user_id) |
            (User.contact_number == user_id)
        ).first()
        
        if user:
            # Generate OTP
            otp = ''.join(random.choices('0123456789', k=6))  # Example 6-digit OTP
            
            # Set OTP and expiry time for the user
            user.otp = otp
            user.otp_expiry = datetime.datetime.now() + datetime.timedelta(minutes=2)  # OTP valid for 2 minutes
            db.session.commit()

            # Send OTP email
            send_otp_email(user.email, otp)
            
            flash('An OTP has been sent to your registered email/phone.', 'success')
            return redirect(url_for('user.verify_otp'))
        else:
            flash('User not found. Please check your details and try again.', 'danger')

    return render_template('forget_password.html')


@user_bp.route('/user/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp = request.form.get('otp')
        user = User.query.filter_by(otp=otp, otp_expiry__gt=datetime.datetime.now()).first()

        if user:
            session['otp'] = otp  # Store OTP in session
            return redirect(url_for('user.change_password'))
        else:
            flash('Invalid or expired OTP.', 'danger')

    return render_template('verify_otp.html')

@user_bp.route('/user/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password == confirm_password:
            otp = session.get('otp')
            user = User.query.filter_by(otp=otp).first()

            if user:
                user.password = generate_password_hash(new_password)
                user.otp = None
                user.otp_expiry = None
                db.session.commit()
                session.pop('otp', None)
                flash('Password changed successfully. You can now log in.', 'success')
                return redirect(url_for('user.login'))
            else:
                flash('User not found.', 'danger')
        else:
            flash('Passwords do not match.', 'danger')

    return render_template('change_password.html')

def send_otp_email(email, otp):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'maxxhospitalpanschell@gmail.com'
    smtp_password = 'Q1w2e3r4@#'
    
    subject = 'Your OTP Code'
    body = f'Your OTP code is {otp}. This code is valid for 2 minutes.'

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            print(f'OTP sent to {email}')
    except Exception as e:
        print(f'Failed to send email: {e}')
