from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User
admin_bp = Blueprint('admin', __name__)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('adminpassword', method='pbkdf2:sha256')

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['user_id'] = ADMIN_USERNAME  # Set user session
            return redirect(url_for('admin.admin_dashboard'))
        elif username != ADMIN_USERNAME:
            flash('Username is not correct', 'danger')
        else:
            flash('Password is wrong', 'danger')
        return redirect(url_for('admin.login'))

    return render_template('admin_login.html')

@admin_bp.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session:  # Check if user is logged in
        flash('You need to log in first.', 'warning')
        return redirect(url_for('admin.login'))

    search_query = request.args.get('search', '')  # Get the search query from the URL parameters
    if search_query:
        users = User.query.filter(
            User.username.like(f'%{search_query}%') |
            User.name.like(f'%{search_query}%') |
            User.email.like(f'%{search_query}%')
        ).all()
    else:
        users = User.query.all()

    return render_template('admin_dashboard.html', users=users, search_query=search_query)

@admin_bp.route('/admin/accept_user/<int:user_id>', methods=['POST'])
def accept_user(user_id):
    if 'user_id' not in session:  # Check if user is logged in
        flash('You need to log in first.', 'warning')
        return redirect(url_for('admin.login'))

    user = User.query.get_or_404(user_id)
    user.accepted = True
    db.session.commit()
    flash('User has been accepted.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/reject_user/<int:user_id>', methods=['POST'])
def reject_user(user_id):
    if 'user_id' not in session:  # Check if user is logged in
        flash('You need to log in first.', 'warning')
        return redirect(url_for('admin.login'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User has been rejected and removed.', 'danger')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/logout')
def logout():
    session.pop('user_id', None)  # Clear user session
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin.login'))

