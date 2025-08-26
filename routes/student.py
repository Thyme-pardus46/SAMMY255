from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Application, Placement, Report, Organization, Notification
from datetime import datetime, date
import os
import json

student_bp = Blueprint('student', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_student_access():
    if not current_user.is_authenticated or current_user.role != 'student':
        flash('Access denied. Student account required.', 'error')
        return False
    return True

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_student_access():
        return redirect(url_for('index'))
    
    # Get student's applications
    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.applied_at.desc()).all()
    
    # Get recent reports
    recent_reports = Report.query.filter_by(student_id=current_user.id).order_by(Report.submitted_at.desc()).limit(5).all()
    
    # Get notifications
    notifications = Notification.query.filter_by(recipient_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Statistics
    stats = {
        'total_applications': len(applications),
        'pending_applications': len([a for a in applications if a.status == 'pending']),
        'approved_applications': len([a for a in applications if a.status == 'approved']),
        'in_progress_applications': len([a for a in applications if a.status == 'in_progress']),
        'total_reports': Report.query.filter_by(student_id=current_user.id).count()
    }
    
    return render_template('student/dashboard.html', 
                         applications=applications, 
                         recent_reports=recent_reports,
                         notifications=notifications,
                         stats=stats)

@student_bp.route('/applications')
@login_required
def applications():
    if not check_student_access():
        return redirect(url_for('index'))
    
    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.applied_at.desc()).all()
    return render_template('student/applications.html', applications=applications)

@student_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    if not check_student_access():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data
        application_type = request.form.get('application_type')
        preferred_location = request.form.get('preferred_location')
        cover_letter = request.form.get('cover_letter')
        placement_id = request.form.get('placement_id')
        
        # Validation
        errors = []
        if not application_type:
            errors.append('Please select an application type')
        if not preferred_location:
            errors.append('Please enter your preferred location')
        if not cover_letter:
            errors.append('Please write a cover letter')
        
        # Handle file uploads
        cv_filename = None
        additional_docs = []
        
        if 'cv' in request.files:
            cv_file = request.files['cv']
            if cv_file and cv_file.filename != '':
                if allowed_file(cv_file.filename):
                    cv_filename = secure_filename(cv_file.filename)
                    cv_filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{cv_filename}"
                    cv_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], cv_filename))
                else:
                    errors.append('Invalid CV file format')
        
        # Handle additional documents
        if 'additional_docs' in request.files:
            files = request.files.getlist('additional_docs')
            for file in files:
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                        additional_docs.append(filename)
                    else:
                        errors.append(f'Invalid file format: {file.filename}')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('student/apply.html', placements=get_available_placements())
        
        # Create application
        try:
            application = Application(
                student_id=current_user.id,
                application_type=application_type,
                preferred_location=preferred_location,
                cover_letter=cover_letter,
                cv_filename=cv_filename,
                additional_documents=json.dumps(additional_docs) if additional_docs else None
            )
            
            if placement_id and placement_id.isdigit():
                application.placement_id = int(placement_id)
            
            db.session.add(application)
            db.session.commit()
            
            # Create notification for admins
            admin_users = User.query.filter_by(role='admin').all()
            for admin in admin_users:
                notification = Notification(
                    recipient_id=admin.id,
                    title='New Application Submitted',
                    message=f'New {application_type} application from {current_user.full_name}',
                    type='info'
                )
                db.session.add(notification)
            
            db.session.commit()
            
            flash('Application submitted successfully!', 'success')
            return redirect(url_for('student.applications'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to submit application. Please try again.', 'error')
            print(f"Application submission error: {e}")
    
    placements = get_available_placements()
    return render_template('student/apply.html', placements=placements)

@student_bp.route('/application/<int:application_id>')
@login_required
def view_application(application_id):
    if not check_student_access():
        return redirect(url_for('index'))
    
    application = Application.query.filter_by(id=application_id, student_id=current_user.id).first_or_404()
    return render_template('student/view_application.html', application=application)

@student_bp.route('/reports')
@login_required
def reports():
    if not check_student_access():
        return redirect(url_for('index'))
    
    reports = Report.query.filter_by(student_id=current_user.id).order_by(Report.submitted_at.desc()).all()
    return render_template('student/reports.html', reports=reports)

@student_bp.route('/submit-report', methods=['GET', 'POST'])
@login_required
def submit_report():
    if not check_student_access():
        return redirect(url_for('index'))
    
    # Get active applications
    active_applications = Application.query.filter_by(
        student_id=current_user.id, 
        status='in_progress'
    ).all()
    
    if not active_applications:
        flash('No active placements found. You need an approved placement to submit reports.', 'warning')
        return redirect(url_for('student.reports'))
    
    if request.method == 'POST':
        # Get form data
        application_id = request.form.get('application_id')
        report_type = request.form.get('report_type')
        week_number = request.form.get('week_number')
        title = request.form.get('title')
        content = request.form.get('content')
        activities = request.form.get('activities')
        challenges = request.form.get('challenges')
        learning_outcomes = request.form.get('learning_outcomes')
        
        # Validation
        errors = []
        if not all([application_id, report_type, title, content]):
            errors.append('Please fill in all required fields')
        
        if report_type == 'weekly' and not week_number:
            errors.append('Week number is required for weekly reports')
        
        # Verify application belongs to student
        application = Application.query.filter_by(
            id=application_id, 
            student_id=current_user.id, 
            status='in_progress'
        ).first()
        
        if not application:
            errors.append('Invalid application selected')
        
        # Handle file attachments
        attachments = []
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filename = f"report_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                        attachments.append(filename)
                    else:
                        errors.append(f'Invalid file format: {file.filename}')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('student/submit_report.html', applications=active_applications)
        
        # Create report
        try:
            report = Report(
                application_id=application_id,
                student_id=current_user.id,
                report_type=report_type,
                week_number=int(week_number) if week_number else None,
                title=title,
                content=content,
                activities=activities,
                challenges=challenges,
                learning_outcomes=learning_outcomes,
                attachments=json.dumps(attachments) if attachments else None
            )
            
            db.session.add(report)
            db.session.commit()
            
            # Notify supervisor
            if application.supervisor:
                notification = Notification(
                    recipient_id=application.supervisor.id,
                    title='New Report Submitted',
                    message=f'New {report_type} report from {current_user.full_name}',
                    type='info'
                )
                db.session.add(notification)
                db.session.commit()
            
            flash('Report submitted successfully!', 'success')
            return redirect(url_for('student.reports'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to submit report. Please try again.', 'error')
            print(f"Report submission error: {e}")
    
    return render_template('student/submit_report.html', applications=active_applications)

@student_bp.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    if not check_student_access():
        return redirect(url_for('index'))
    
    report = Report.query.filter_by(id=report_id, student_id=current_user.id).first_or_404()
    return render_template('student/view_report.html', report=report)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not check_student_access():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Update profile information
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.course = request.form.get('course', '').strip()
        current_user.university = request.form.get('university', '').strip()
        current_user.department = request.form.get('department', '').strip()
        
        year_of_study = request.form.get('year_of_study')
        if year_of_study:
            try:
                current_user.year_of_study = int(year_of_study)
            except ValueError:
                flash('Invalid year of study', 'error')
                return render_template('student/profile.html')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('student/profile.html')

@student_bp.route('/notifications')
@login_required
def notifications():
    if not check_student_access():
        return redirect(url_for('index'))
    
    notifications = Notification.query.filter_by(recipient_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark notifications as read
    unread_notifications = [n for n in notifications if not n.is_read]
    for notification in unread_notifications:
        notification.is_read = True
    
    if unread_notifications:
        db.session.commit()
    
    return render_template('student/notifications.html', notifications=notifications)

def get_available_placements():
    """Get available placements for students to apply to"""
    return Placement.query.filter(
        Placement.is_active == True,
        Placement.available_slots > Placement.filled_slots
    ).order_by(Placement.created_at.desc()).all()