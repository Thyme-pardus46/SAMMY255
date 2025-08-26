from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Application, Placement, Organization, Evaluation, Notification
from datetime import datetime, date

organization_bp = Blueprint('organization', __name__)

def check_organization_access():
    if not current_user.is_authenticated or current_user.role != 'organization':
        flash('Access denied. Organization account required.', 'error')
        return False
    return True

@organization_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Get organization's placements
    placements = Placement.query.join(Organization).filter(
        Organization.name == current_user.organization_name
    ).all()
    
    # Get applications to organization's placements
    placement_ids = [p.id for p in placements]
    applications = Application.query.filter(Application.placement_id.in_(placement_ids)).all() if placement_ids else []
    
    # Get notifications
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Statistics
    stats = {
        'total_placements': len(placements),
        'active_placements': len([p for p in placements if p.is_active]),
        'total_applications': len(applications),
        'pending_applications': len([a for a in applications if a.status == 'pending']),
        'active_students': len([a for a in applications if a.status == 'in_progress'])
    }
    
    return render_template('organization/dashboard.html', 
                         placements=placements,
                         applications=applications[:5],  # Recent applications
                         notifications=notifications,
                         stats=stats)

@organization_bp.route('/placements')
@login_required
def placements():
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Get organization record
    organization = Organization.query.filter_by(name=current_user.organization_name).first()
    
    if not organization:
        flash('Organization not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    placements = Placement.query.filter_by(organization_id=organization.id).order_by(Placement.created_at.desc()).all()
    return render_template('organization/placements.html', placements=placements)

@organization_bp.route('/add-placement', methods=['GET', 'POST'])
@login_required
def add_placement():
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Get organization record
    organization = Organization.query.filter_by(name=current_user.organization_name).first()
    
    if not organization:
        flash('Organization not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        requirements = request.form.get('requirements', '').strip()
        available_slots = request.form.get('available_slots')
        
        # Validation
        if not all([title, location, available_slots]):
            flash('Please fill in all required fields', 'error')
            return render_template('organization/add_placement.html')
        
        try:
            placement = Placement(
                title=title,
                description=description,
                organization_id=organization.id,
                location=location,
                requirements=requirements,
                available_slots=int(available_slots)
            )
            
            if start_date:
                placement.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                placement.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            db.session.add(placement)
            db.session.commit()
            
            flash('Placement opportunity added successfully!', 'success')
            return redirect(url_for('organization.placements'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to add placement. Please try again.', 'error')
            print(f"Add placement error: {e}")
    
    return render_template('organization/add_placement.html')

@organization_bp.route('/applications')
@login_required
def applications():
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Get organization's placements
    organization = Organization.query.filter_by(name=current_user.organization_name).first()
    
    if not organization:
        flash('Organization not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get applications to organization's placements
    placement_ids = [p.id for p in organization.placements]
    applications = Application.query.filter(Application.placement_id.in_(placement_ids)).order_by(Application.applied_at.desc()).all() if placement_ids else []
    
    return render_template('organization/applications.html', applications=applications)

@organization_bp.route('/application/<int:application_id>')
@login_required
def view_application(application_id):
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Verify application belongs to organization's placement
    organization = Organization.query.filter_by(name=current_user.organization_name).first()
    
    if not organization:
        flash('Organization not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    placement_ids = [p.id for p in organization.placements]
    application = Application.query.filter(
        Application.id == application_id,
        Application.placement_id.in_(placement_ids)
    ).first_or_404()
    
    return render_template('organization/view_application.html', application=application)

@organization_bp.route('/respond-application/<int:application_id>', methods=['POST'])
@login_required
def respond_application(application_id):
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Verify application belongs to organization's placement
    organization = Organization.query.filter_by(name=current_user.organization_name).first()
    
    if not organization:
        flash('Organization not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    placement_ids = [p.id for p in organization.placements]
    application = Application.query.filter(
        Application.id == application_id,
        Application.placement_id.in_(placement_ids)
    ).first_or_404()
    
    action = request.form.get('action')
    comments = request.form.get('comments', '').strip()
    
    try:
        if action == 'accept':
            # Check if placement has available slots
            if application.placement.filled_slots >= application.placement.available_slots:
                flash('No available slots for this placement', 'error')
                return redirect(url_for('organization.view_application', application_id=application_id))
            
            # Update placement filled slots
            application.placement.filled_slots += 1
            
            # Notify admins for final approval
            admin_users = User.query.filter_by(role='admin').all()
            for admin in admin_users:
                notification = Notification(
                    recipient_id=admin.id,
                    title='Application Accepted by Organization',
                    message=f'Application from {application.student.full_name} has been accepted by {organization.name}',
                    type='info'
                )
                db.session.add(notification)
        
        elif action == 'reject':
            pass  # No additional actions needed for rejection
        
        else:
            flash('Invalid action', 'error')
            return redirect(url_for('organization.view_application', application_id=application_id))
        
        # Add organization comments
        if not application.admin_comments:
            application.admin_comments = f"Organization Response: {comments}"
        else:
            application.admin_comments += f"\n\nOrganization Response: {comments}"
        
        db.session.commit()
        
        # Notify student
        notification = Notification(
            recipient_id=application.student_id,
            title='Application Response from Organization',
            message=f'Your application to {organization.name} has been {action}ed',
            type='success' if action == 'accept' else 'warning'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Application {action}ed successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to respond to application. Please try again.', 'error')
        print(f"Application response error: {e}")
    
    return redirect(url_for('organization.view_application', application_id=application_id))

@organization_bp.route('/students')
@login_required
def students():
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Get students placed at this organization
    organization = Organization.query.filter_by(name=current_user.organization_name).first()
    
    if not organization:
        flash('Organization not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    placement_ids = [p.id for p in organization.placements]
    active_students = Application.query.filter(
        Application.placement_id.in_(placement_ids),
        Application.status == 'in_progress'
    ).all() if placement_ids else []
    
    return render_template('organization/students.html', applications=active_students)

@organization_bp.route('/evaluate/<int:application_id>', methods=['GET', 'POST'])
@login_required
def evaluate_student(application_id):
    if not check_organization_access():
        return redirect(url_for('index'))
    
    # Verify application belongs to organization's placement
    organization = Organization.query.filter_by(name=current_user.organization_name).first()
    
    if not organization:
        flash('Organization not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    placement_ids = [p.id for p in organization.placements]
    application = Application.query.filter(
        Application.id == application_id,
        Application.placement_id.in_(placement_ids),
        Application.status == 'in_progress'
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
            return render_template('organization/evaluate_student.html', application=application)
        
        try:
            evaluation_date = datetime.strptime(evaluation_date, '%Y-%m-%d').date()
            
            evaluation = Evaluation(
                application_id=application_id,
                evaluator_id=current_user.id,
                evaluator_type='organization',
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
            
            # Notify student and supervisor
            notifications = [
                Notification(
                    recipient_id=application.student_id,
                    title='New Evaluation from Organization',
                    message=f'You have received a new evaluation from {organization.name}',
                    type='info'
                )
            ]
            
            if application.supervisor:
                notifications.append(Notification(
                    recipient_id=application.supervisor_id,
                    title='Organization Evaluation',
                    message=f'Organization evaluation completed for {application.student.full_name}',
                    type='info'
                ))
            
            for notification in notifications:
                db.session.add(notification)
            
            db.session.commit()
            
            flash('Evaluation submitted successfully!', 'success')
            return redirect(url_for('organization.students'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to submit evaluation. Please try again.', 'error')
            print(f"Evaluation submission error: {e}")
    
    return render_template('organization/evaluate_student.html', application=application)

@organization_bp.route('/notifications')
@login_required
def notifications():
    if not check_organization_access():
        return redirect(url_for('index'))
    
    notifications = Notification.query.filter_by(recipient_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark notifications as read
    unread_notifications = [n for n in notifications if not n.is_read]
    for notification in unread_notifications:
        notification.is_read = True
    
    if unread_notifications:
        db.session.commit()
    
    return render_template('organization/notifications.html', notifications=notifications)

@organization_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not check_organization_access():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.organization_name = request.form.get('organization_name', '').strip()
        current_user.organization_type = request.form.get('organization_type', '').strip()
        current_user.registration_number = request.form.get('registration_number', '').strip()
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('organization/profile.html')