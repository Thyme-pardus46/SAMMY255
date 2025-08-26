from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Application, Report, Notification, Evaluation, Attendance
from datetime import datetime, date
import json

supervisor_bp = Blueprint('supervisor', __name__)

def check_supervisor_access():
    if not current_user.is_authenticated or current_user.role != 'supervisor':
        flash('Access denied. Supervisor account required.', 'error')
        return False
    return True

@supervisor_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    # Get assigned students
    assigned_applications = Application.query.filter_by(supervisor_id=current_user.id).all()
    
    # Get pending reports
    pending_reports = Report.query.join(Application).filter(
        Application.supervisor_id == current_user.id,
        Report.status == 'submitted'
    ).order_by(Report.submitted_at.desc()).limit(10).all()
    
    # Get notifications
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Statistics
    stats = {
        'total_students': len(assigned_applications),
        'active_students': len([a for a in assigned_applications if a.status == 'in_progress']),
        'pending_reports': len(pending_reports),
        'completed_placements': len([a for a in assigned_applications if a.status == 'completed'])
    }
    
    return render_template('supervisor/dashboard.html', 
                         applications=assigned_applications,
                         pending_reports=pending_reports,
                         notifications=notifications,
                         stats=stats)

@supervisor_bp.route('/students')
@login_required
def students():
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    assigned_applications = Application.query.filter_by(supervisor_id=current_user.id).order_by(Application.start_date.desc()).all()
    return render_template('supervisor/students.html', applications=assigned_applications)

@supervisor_bp.route('/student/<int:application_id>')
@login_required
def view_student(application_id):
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    application = Application.query.filter_by(
        id=application_id, 
        supervisor_id=current_user.id
    ).first_or_404()
    
    # Get student's reports
    reports = Report.query.filter_by(application_id=application_id).order_by(Report.submitted_at.desc()).all()
    
    # Get attendance records
    attendance_records = Attendance.query.filter_by(application_id=application_id).order_by(Attendance.date.desc()).all()
    
    # Get evaluations
    evaluations = Evaluation.query.filter_by(
        application_id=application_id,
        evaluator_id=current_user.id
    ).order_by(Evaluation.created_at.desc()).all()
    
    return render_template('supervisor/view_student.html', 
                         application=application,
                         reports=reports,
                         attendance_records=attendance_records,
                         evaluations=evaluations)

@supervisor_bp.route('/reports')
@login_required
def reports():
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    # Get all reports from supervised students
    reports = Report.query.join(Application).filter(
        Application.supervisor_id == current_user.id
    ).order_by(Report.submitted_at.desc()).all()
    
    return render_template('supervisor/reports.html', reports=reports)

@supervisor_bp.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    report = Report.query.join(Application).filter(
        Report.id == report_id,
        Application.supervisor_id == current_user.id
    ).first_or_404()
    
    return render_template('supervisor/view_report.html', report=report)

@supervisor_bp.route('/approve-report/<int:report_id>', methods=['POST'])
@login_required
def approve_report(report_id):
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    report = Report.query.join(Application).filter(
        Report.id == report_id,
        Application.supervisor_id == current_user.id
    ).first_or_404()
    
    feedback = request.form.get('feedback', '').strip()
    rating = request.form.get('rating')
    action = request.form.get('action')  # 'approve' or 'revision'
    
    try:
        if action == 'approve':
            report.status = 'approved'
        elif action == 'revision':
            report.status = 'revision_required'
        else:
            flash('Invalid action', 'error')
            return redirect(url_for('supervisor.view_report', report_id=report_id))
        
        report.supervisor_feedback = feedback
        if rating and rating.isdigit():
            report.supervisor_rating = int(rating)
        report.feedback_date = datetime.utcnow()
        
        db.session.commit()
        
        # Notify student
        notification = Notification(
            recipient_id=report.student_id,
            title='Report Feedback',
            message=f'Your {report.report_type} report has been {report.status}',
            type='info' if report.status == 'approved' else 'warning'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Report {report.status} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update report. Please try again.', 'error')
        print(f"Report approval error: {e}")
    
    return redirect(url_for('supervisor.view_report', report_id=report_id))

@supervisor_bp.route('/attendance/<int:application_id>')
@login_required
def attendance(application_id):
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    application = Application.query.filter_by(
        id=application_id, 
        supervisor_id=current_user.id
    ).first_or_404()
    
    attendance_records = Attendance.query.filter_by(
        application_id=application_id
    ).order_by(Attendance.date.desc()).all()
    
    return render_template('supervisor/attendance.html', 
                         application=application,
                         attendance_records=attendance_records)

@supervisor_bp.route('/record-attendance/<int:application_id>', methods=['GET', 'POST'])
@login_required
def record_attendance(application_id):
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    application = Application.query.filter_by(
        id=application_id, 
        supervisor_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        attendance_date = request.form.get('date')
        status = request.form.get('status')
        check_in_time = request.form.get('check_in_time')
        check_out_time = request.form.get('check_out_time')
        notes = request.form.get('notes', '').strip()
        
        # Validation
        errors = []
        if not attendance_date:
            errors.append('Please select a date')
        if not status:
            errors.append('Please select attendance status')
        
        try:
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Invalid date format')
        
        # Check for duplicate attendance record
        existing_record = Attendance.query.filter_by(
            application_id=application_id,
            date=attendance_date
        ).first()
        
        if existing_record:
            errors.append('Attendance record for this date already exists')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('supervisor/record_attendance.html', application=application)
        
        try:
            # Parse times if provided
            check_in_parsed = None
            check_out_parsed = None
            
            if check_in_time:
                check_in_parsed = datetime.strptime(check_in_time, '%H:%M').time()
            if check_out_time:
                check_out_parsed = datetime.strptime(check_out_time, '%H:%M').time()
            
            attendance_record = Attendance(
                application_id=application_id,
                date=attendance_date,
                status=status,
                check_in_time=check_in_parsed,
                check_out_time=check_out_parsed,
                notes=notes,
                recorded_by=current_user.id
            )
            
            db.session.add(attendance_record)
            db.session.commit()
            
            flash('Attendance recorded successfully!', 'success')
            return redirect(url_for('supervisor.attendance', application_id=application_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to record attendance. Please try again.', 'error')
            print(f"Attendance recording error: {e}")
    
    return render_template('supervisor/record_attendance.html', application=application)

@supervisor_bp.route('/evaluate/<int:application_id>', methods=['GET', 'POST'])
@login_required
def evaluate_student(application_id):
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    application = Application.query.filter_by(
        id=application_id, 
        supervisor_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        # Get evaluation criteria (1-5 scale)
        punctuality = request.form.get('punctuality')
        professionalism = request.form.get('professionalism')
        communication = request.form.get('communication')
        technical_skills = request.form.get('technical_skills')
        teamwork = request.form.get('teamwork')
        initiative = request.form.get('initiative')
        overall_performance = request.form.get('overall_performance')
        
        # Get feedback
        strengths = request.form.get('strengths', '').strip()
        areas_for_improvement = request.form.get('areas_for_improvement', '').strip()
        additional_comments = request.form.get('additional_comments', '').strip()
        recommendation = request.form.get('recommendation')
        evaluation_date = request.form.get('evaluation_date')
        
        # Validation
        errors = []
        required_ratings = [punctuality, professionalism, communication, technical_skills, 
                          teamwork, initiative, overall_performance]
        
        if not all(required_ratings):
            errors.append('Please provide all ratings')
        
        if not evaluation_date:
            errors.append('Please select evaluation date')
        
        if not recommendation:
            errors.append('Please select a recommendation')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('supervisor/evaluate_student.html', application=application)
        
        try:
            evaluation_date = datetime.strptime(evaluation_date, '%Y-%m-%d').date()
            
            evaluation = Evaluation(
                application_id=application_id,
                evaluator_id=current_user.id,
                evaluator_type='supervisor',
                punctuality=int(punctuality),
                professionalism=int(professionalism),
                communication=int(communication),
                technical_skills=int(technical_skills),
                teamwork=int(teamwork),
                initiative=int(initiative),
                overall_performance=int(overall_performance),
                strengths=strengths,
                areas_for_improvement=areas_for_improvement,
                additional_comments=additional_comments,
                recommendation=recommendation,
                evaluation_date=evaluation_date
            )
            
            db.session.add(evaluation)
            db.session.commit()
            
            # Notify student
            notification = Notification(
                recipient_id=application.student_id,
                title='New Evaluation',
                message=f'Your supervisor has submitted a new evaluation for your placement',
                type='info'
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Evaluation submitted successfully!', 'success')
            return redirect(url_for('supervisor.view_student', application_id=application_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to submit evaluation. Please try again.', 'error')
            print(f"Evaluation submission error: {e}")
    
    return render_template('supervisor/evaluate_student.html', application=application)

@supervisor_bp.route('/notifications')
@login_required
def notifications():
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    notifications = Notification.query.filter_by(recipient_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark notifications as read
    unread_notifications = [n for n in notifications if not n.is_read]
    for notification in unread_notifications:
        notification.is_read = True
    
    if unread_notifications:
        db.session.commit()
    
    return render_template('supervisor/notifications.html', notifications=notifications)

@supervisor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not check_supervisor_access():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('supervisor/profile.html')