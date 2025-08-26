# Field Supervision Management System

A comprehensive web application designed for universities and colleges in Africa to manage student field placements, internships, and teaching practice supervision.

## Features

### 🎓 Student Module
- **Registration & Login**: Secure account creation with role-based access
- **Application Management**: Online application submission for field placements
- **Document Upload**: CV, placement request forms, and supporting documents
- **Progress Tracking**: Real-time status updates on applications
- **Report Submission**: Weekly/monthly field reports and logs
- **Communication**: Direct communication with supervisors and administrators

### 👨‍🏫 Supervisor Module
- **Student Oversight**: View and manage assigned students
- **Report Review**: Approve/decline student reports with feedback
- **Attendance Tracking**: Monitor student attendance during placements
- **Performance Evaluation**: Comprehensive student performance assessments
- **Communication Tools**: Feedback and guidance for students

### 🏛️ Administrator Module
- **Application Management**: Review, approve, or reject student applications
- **Supervisor Assignment**: Assign supervisors to approved placements
- **Organization Management**: Manage partner organizations and companies
- **Reporting & Analytics**: Generate comprehensive reports and statistics
- **User Management**: Activate/deactivate user accounts

### 🏢 Organization Module
- **Placement Opportunities**: Create and manage internship/field opportunities
- **Application Review**: Accept or reject student placement applications
- **Student Evaluation**: Provide feedback on student performance
- **Collaboration**: Work with universities for student development

## Technical Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: SQLite (easily configurable for PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5 with responsive design
- **Authentication**: Flask-Login with secure password hashing
- **File Handling**: Secure file uploads and management
- **Notifications**: Real-time notification system
- **Export**: PDF and Excel report generation

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project files**
   ```bash
   cd /workspace
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional)
   ```bash
   export EMAIL_USER=your-email@gmail.com
   export EMAIL_PASS=your-app-password
   ```

4. **Initialize the database**
   ```bash
   python app.py
   ```
   The database will be created automatically on first run.

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your web browser and navigate to: `http://localhost:5000`

## Default Setup

### Creating Admin Account
After starting the application, register the first user with the role "supervisor" and manually change their role to "admin" in the database, or create an admin user programmatically.

### Sample Data
The application starts with an empty database. You can:
- Register test users for different roles
- Create sample organizations and placements
- Test the complete workflow

## Usage Guide

### For Students
1. **Register** with your student details
2. **Complete your profile** with university information
3. **Browse available placements** or apply generally
4. **Submit applications** with required documents
5. **Track application status** through your dashboard
6. **Submit regular reports** during field placement

### For Supervisors
1. **Register** as a supervisor
2. **View assigned students** in your dashboard
3. **Review and approve reports** submitted by students
4. **Track student attendance** and performance
5. **Provide evaluations** and feedback

### For Administrators
1. **Manage all applications** from the admin dashboard
2. **Assign supervisors** to approved applications
3. **Add organizations** and placement opportunities
4. **Generate reports** for institutional analysis
5. **Monitor system usage** and user activity

### For Organizations
1. **Register** as an organization representative
2. **Create placement opportunities** for students
3. **Review applications** from interested students
4. **Evaluate student performance** during placements
5. **Collaborate** with universities for mutual benefit

## Configuration

### Email Settings
To enable email notifications, configure your email settings in `app.py`:
```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'
```

### Database Configuration
By default, the application uses SQLite. To use PostgreSQL or MySQL:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/dbname'
# or
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:password@localhost/dbname'
```

### File Upload Settings
Configure file upload limits and allowed extensions in `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = 'uploads'
```

## Security Features

- **Password Security**: Bcrypt hashing with strength validation
- **Role-based Access Control**: Strict separation of user roles
- **CSRF Protection**: Forms protected against cross-site request forgery
- **File Upload Security**: Validated file types and secure storage
- **SQL Injection Prevention**: SQLAlchemy ORM protection

## Mobile Responsiveness

The application is fully responsive and works seamlessly on:
- Desktop computers
- Tablets
- Smartphones
- Various screen sizes and orientations

## Support & Customization

This system is designed to be:
- **Scalable**: Handles growing numbers of users and institutions
- **Customizable**: Easy to modify for specific institutional needs
- **Maintainable**: Clean code structure for future development
- **Extensible**: Add new features and integrations

## African Context Features

- **Multi-institutional Support**: Designed for university consortiums
- **Flexible Placement Types**: Teaching practice, internships, industrial attachments
- **Local Organization Integration**: Support for government, NGO, and private sector partnerships
- **Cultural Considerations**: UI and workflow designed for African educational contexts

## Deployment

### Production Deployment
For production deployment, consider:
- Use a production WSGI server like Gunicorn
- Configure a reverse proxy with Nginx
- Use a production database (PostgreSQL recommended)
- Set up SSL/TLS encryption
- Configure backup strategies
- Monitor application performance

### Example Production Command
```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is designed for educational institutions across Africa. Please contact the development team for licensing information.

## Contact

For support, customization, or deployment assistance, please contact the development team.

---

**Empowering African Education Through Technology** 🌍

This system represents a commitment to improving educational outcomes across Africa by streamlining field supervision and creating stronger partnerships between universities and organizations.