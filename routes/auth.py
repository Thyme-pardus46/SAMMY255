from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, db
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # At least 8 characters, one uppercase, one lowercase, one digit
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact administrator.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()
        
        # Student-specific fields
        student_id = request.form.get('student_id', '').strip()
        course = request.form.get('course', '').strip()
        year_of_study = request.form.get('year_of_study')
        university = request.form.get('university', '').strip()
        department = request.form.get('department', '').strip()
        
        # Organization-specific fields
        organization_name = request.form.get('organization_name', '').strip()
        organization_type = request.form.get('organization_type', '').strip()
        registration_number = request.form.get('registration_number', '').strip()
        
        # Validation
        errors = []
        
        if not all([email, password, first_name, last_name, role]):
            errors.append('Please fill in all required fields')
        
        if not validate_email(email):
            errors.append('Please enter a valid email address')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            errors.append(password_message)
        
        if role not in ['student', 'supervisor', 'organization']:
            errors.append('Please select a valid role')
        
        # Role-specific validation
        if role == 'student':
            if not all([student_id, course, university, department]):
                errors.append('Please fill in all student fields')
            if year_of_study:
                try:
                    year_of_study = int(year_of_study)
                    if year_of_study < 1 or year_of_study > 7:
                        errors.append('Year of study must be between 1 and 7')
                except ValueError:
                    errors.append('Year of study must be a number')
        
        elif role == 'organization':
            if not all([organization_name, organization_type]):
                errors.append('Please fill in all organization fields')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            errors.append('Email address already registered')
        
        # Check if student ID already exists (for students)
        if role == 'student' and student_id:
            if User.query.filter_by(student_id=student_id).first():
                errors.append('Student ID already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role
            )
            new_user.set_password(password)
            
            # Set role-specific fields
            if role == 'student':
                new_user.student_id = student_id
                new_user.course = course
                new_user.year_of_study = year_of_study
                new_user.university = university
                new_user.department = department
            elif role == 'organization':
                new_user.organization_name = organization_name
                new_user.organization_type = organization_type
                new_user.registration_number = registration_number
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # In a real application, you would send a password reset email here
            flash('Password reset instructions have been sent to your email.', 'info')
        else:
            flash('No account found with that email address.', 'error')
    
    return render_template('auth/forgot_password.html')