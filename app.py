from datetime import timedelta
import json
import subprocess
from flask import Flask, jsonify, make_response, render_template, render_template_string, url_for, flash, redirect, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,joinedload
from sqlalchemy.exc import IntegrityError

from auth import require_role,get_user_from_token,gen_token,SECRET_KEY,PORT
from forms import *
from models import *
from werkzeug.utils import secure_filename
import os
from faker import Faker

fake = Faker()

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'static', 'pdfs')
app.config['SCRIPTS_FOLDER'] = os.path.join(base_dir, 'static', 'scripts')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=3)
app.secret_key = SECRET_KEY
ALLOWED_EXTENSIONS = {'pdf'}
engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    session = Session()
    user, _ = get_user_from_token()

    # Retrieve all projects with eager loading of 'teacher' and 'students' attributes
    projects = session.query(Project).options(joinedload(Project.teacher), joinedload(Project.students)).all()
    #print(projects[0].teacher)
    session.close()

    return render_template('home.html', current_user=user, projects=projects)


@app.route('/about')
def about():
    user,_ = get_user_from_token()
    return render_template('about.html',current_user=user)

# Login endpoint
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Get the submitted username and password
        username = form.username.data
        password = form.password.data
        
        # Create a new database session
        session = Session()
        
        try:
            # Query the user with the given username
            user = session.query(User).filter_by(username=username).first()
            
            if user:
                # Verify the password
                if user.check_password(password):
                    # Generate a JWT token for authentication
                    token = gen_token(username, user.role)
                    
                    # Set the token as a cookie
                    response = redirect('/dashboard')
                    response.set_cookie('token', token)
                    
                    return response
                else:
                    # Flash an error message for invalid password
                    flash('Invalid password.', 'danger')
            else:
                # Flash an error message for invalid username
                flash('Invalid username.', 'danger')
        
        finally:
            # Close the database session
            session.close()
    
    return render_template('login.html', form=form)


# Registration endpoint
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Get the submitted username and password
        username = form.username.data
        password = form.password.data
        
        # Create a new student object
        student = Student(username=username, password=password)
        
        # Create a new database session
        session = Session()
        
        try:
            # Add the student to the database
            session.add(student)
            session.commit()
            
            # Flash a success message
            flash('Registration successful! You can now log in.', 'success')
            
            # Redirect the user to the login page
            return redirect('/login')
        
        except:
            # Rollback the changes in case of any error
            session.rollback()
            raise
        
        finally:
            # Close the database session
            session.close()

    return render_template('register.html', form=form)

@app.route('/request/update-role', methods=['POST'])
@require_role(['student', 'teacher'])
def request_update_role():
    form = RequestForm()
    if form.validate_on_submit():
        request_content = form.content.data
        
        session = Session()
        
        try:
            current_user, current_user_role = get_user_from_token()

            # Retrieve the appropriate database object based on the user's role
            if current_user_role == 'student':
                current_user_obj = session.query(Student).filter_by(username=current_user).first()
            elif current_user_role == 'teacher':
                current_user_obj = session.query(Teacher).filter_by(username=current_user).first()
            else:
                # Handle the case when the user's role is neither student nor teacher
                return render_template('error.html', code="403", message="Invalid Role")

            request_obj = Request(content=request_content, sender=current_user_obj)
            
            session.add(request_obj)
            session.commit()
            
            flash('Request sent successfully!', 'success')
            
        finally:
            session.close()

    return redirect('/dashboard')



# Admin approval endpoint

@app.route('/admin/approve-role/<int:request_id>', methods=['GET'])
@require_role(['admin'])  # Only admins can access this endpoint
def approve_role(request_id):
    # Create a new database session
    session = Session()

    try:
        # Find the request to update
        request_obj = session.query(Request).filter_by(id=request_id).first()

        if request_obj:
            # Retrieve the user associated with the request
            user = session.query(User).filter_by(id=request_obj.sender_id).first()

            if user:
                # Check if the request is to update a student to an admin role
                if request_obj.content == 'admin' and isinstance(user, Student):
                    # Update the role of the user to 'admin'
                    user.role = 'admin'

                    # Commit the changes to the database
                    session.commit()

                    # Delete the request from the database
                    session.delete(request_obj)
                    session.commit()

                    # Flash a success message
                    flash('Role updated successfully!', 'success')

                # Check if the request is to update a teacher to an admin role
                elif request_obj.content == 'admin' and isinstance(user, Teacher):
                    # Update the role of the user to 'admin'
                    user.role = 'admin'

                    # Commit the changes to the database
                    session.commit()

                    # Delete the request from the database
                    session.delete(request_obj)
                    session.commit()

                    # Flash a success message
                    flash('Role updated successfully!', 'success')

                # Check if the request is to update a teacher to a student role
                elif request_obj.content == 'teacher' and isinstance(user, Student):
                    # Update the role of the user to 'teacher'
                    user.role = 'teacher'

                    # Commit the changes to the database
                    session.commit()

                    # Delete the request from the database
                    session.delete(request_obj)
                    session.commit()

                    # Flash a success message
                    flash('Role updated successfully!', 'success')

                else:
                    # Flash an error message if the request content is not recognized
                    flash('Invalid request content!', 'danger')

            else:
                # Flash an error message if the user is not found
                flash('User not found!', 'danger')

        else:
            # Flash an error message if the request is not found
            flash('Request not found!', 'danger')

        return redirect('/admin-dashboard')

    finally:
        # Close the database session
        session.close()


@app.route('/admin/reject-role/<int:request_id>', methods=['GET'])
@require_role(['admin'])  # Only admins can access this endpoint
def reject_role(request_id):
    # Create a new database session
    session = Session()

    try:
        # Find the request to reject
        request_obj = session.query(Request).filter_by(id=request_id).first()

        if request_obj:
            # Delete the request from the database
            session.delete(request_obj)

            # Commit the changes to the database
            session.commit()

            # Flash a success message
            flash('Request rejected successfully!', 'success')
        else:
            # Flash an error message if the request is not found
            flash('Request not found!', 'danger')

    finally:
        # Close the database session
        session.close()

    return redirect('/admin-dashboard')  # Redirect to the admin dashboard or any other appropriate page


@app.route('/dashboard')
@require_role(['admin', 'teacher', 'student'])
def dashboard():
    user, user_role = get_user_from_token()
    if user_role == 'admin':
        return redirect('/admin-dashboard')
    elif user_role == 'teacher':
        return redirect('/teacher-dashboard')
    elif user_role == 'student':
        return redirect('/student-dashboard')
    else:
        return render_template("error.html", code="403", message="Unknown user role",current_user=user)


@app.route('/admin-dashboard')
@require_role(['admin'])  # Only admins can access this endpoint
def admin_dashboard():
    # Create a new database session
    username, role = get_user_from_token()
    session = Session() 
    admin = session.query(Admin).filter(Admin.username == username).first()
    form = UpdateAdminForm()

    try:
        # Retrieve all the requests from the database with sender information
        requests = session.query(Request, User).join(User, Request.sender_id == User.id).all()

        if not requests:
            flash('No requests found!', 'info')

        request_data = [
            {
                'request': request,
                'sender': user,
                'student_id': user.student_id if isinstance(user, Student) else None,
                'role': "Student" if isinstance(user, Student) else "Teacher",
                'teacher_id': user.teacher_id if isinstance(user, Teacher) else None,
            }
            for request, user in requests
        ]

        return render_template('admin_dashboard.html', current_user=admin, requests=request_data, form=form)

    finally:
        # Close the database session
        session.close()





@app.route('/student-dashboard')
@require_role(['student'])
def student_dashboard():
    # Get the logged in student
    username, role = get_user_from_token()
    session = Session()
    student = session.query(Student).filter(Student.username == username).first()
    form = RequestForm()
    form2 = UpdateStudentForm()

    # Retrieve the student's project if available
    project = None
    if len(student.projects) > 0:
    # Code to execute when the student has projects
        # Eager load the students associated with the project
        project = session.query(Project).options(joinedload(Project.students)).filter(Project.students.any(Student.username == username)).first()


    encadrant = student.encadrant

    # Retrieve the student's sprints if project is available
    sprints = project.sprint_entries if project else []

    session.close()

    return render_template('student-dashboard.html', current_user=student, project=project, sprints=sprints, form=form, form2=form2)




@app.route('/teacher-dashboard')
@require_role(['teacher'])
def teacher_dashboard():
    # Get the logged in teacher
    username, role = get_user_from_token()
    session = Session()
    teacher = session.query(Teacher).options(joinedload(Teacher.students)).filter(Teacher.username == username).first()
    sprint_form = SprintForm()
    project_form = ProjectForm()
    form = RequestForm()
    form2 = UpdateTeacherForm()
    update_sprint = UpdateSprintForm()

    # Retrieve all students from the database
    all_students = session.query(Student).all()

    # Populate the students field in the project form with all students
    project_form.students.choices = [(student.id, student.username) for student in all_students]
    sprint_form.project.choices = [(project.id, project.name) for project in teacher.projects]

    # Retrieve the teacher's students
    related_students = teacher.students or []

    # Retrieve all projects from the database
    projects = session.query(Project).options(joinedload(Project.students)).filter_by(teacher_id=teacher.id).all()


    # Retrieve the sprints for each project
    project_sprints = {}
    for project in projects:
        sprints = session.query(Sprint).filter_by(project_id=project.id).all()
        project_sprints[project.id] = sprints

    session.close()

    return render_template('teacher_dashboard.html', current_user=teacher, projects=projects,
                           project_sprints=project_sprints, sprint_form=sprint_form,
                           project_form=project_form, form=form, form2=form2,
                           students=related_students, update_sprint_form=update_sprint)


@app.route('/upload_rapport', methods=['POST'])
@require_role(['student'])
def upload_rapport():
    # Get the logged in student
    username, role = get_user_from_token()
    session = Session()
    student = session.query(Student).filter(Student.username == username).first()

    # Retrieve the student's project
    project = student.projects[0] if student.projects else None

    if not project:
        session.close()
        return render_template("error.html", code="404", message="No project assigned.", current_user=student)

    # Check if the 'rapport' file was uploaded
    if 'rapport' not in request.files:
        session.close()
        return render_template("error.html", code="400", message="No file selected.", current_user=student)

    rapport_file = request.files['rapport']

    # Check if a file was selected
    if rapport_file.filename == '':
        session.close()
        return render_template("error.html", code="400", message="No file selected.", current_user=student)

    # Check if the file is in PDF format
    if not allowed_file(rapport_file.filename):
        session.close()
        return render_template("error.html", code="400", message="Invalid file format. Only PDF files are allowed.", current_user=student)

    # Save the file with a unique name
    filename = secure_filename(rapport_file.filename)
    project_name = project.name.replace(" ", "-")  # Replace spaces with underscores
    teacher_name = project.teacher.username.replace(" ", "-")  # Replace spaces with underscores
    new_filename = f"{project_name}_{teacher_name.lower()}.pdf"
    rapport_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

    if os.path.exists(rapport_path):
        os.remove(rapport_path)  # Remove the existing file

    rapport_file.save(rapport_path)

    # Update the project's rapport URL
    project.rapport = url_for('static', filename='pdfs/' + new_filename)

    session.commit()
    session.close()

    return redirect(url_for('student_dashboard'))




@app.route('/create-sprint', methods=['POST'])
@require_role(['teacher'])
def create_sprint():
    sprint_form = SprintForm(request.form)
    session = Session()
    # Get the logged in student
    username, role = get_user_from_token()
    session = Session()
    teacher = session.query(Teacher).filter(Teacher.username == username).first()
    sprint_form.project.choices = [(project.id, project.name) for project in teacher.projects]
    if sprint_form.validate() and 'submit' in request.form:
        sprint_name = sprint_form.sprint_name.data
        sprint_number = sprint_form.sprint_number.data
        progress = sprint_form.progress.data
        review = sprint_form.review.data
        start_date = sprint_form.start_date.data
        deadline = sprint_form.deadline.data
        project_id = sprint_form.project.data
        sprint = Sprint(sprint_name=sprint_name,sprint_number=sprint_number, progress=progress, review=review, start_date=start_date,
                        deadline=deadline)
        sprint.project_id = project_id
        session.add(sprint)
        session.commit()
        session.refresh(sprint)
        flash('Sprint created successfully', 'success')
        return redirect(url_for('teacher_dashboard'))
    session.close()
    return redirect(url_for('teacher_dashboard'))


@app.route('/update-sprint/<int:sprint_id>', methods=['POST'])
@require_role(['teacher'])
def update_sprint(sprint_id):
    session = Session()
    username, role = get_user_from_token()
    teacher = session.query(Teacher).filter(Teacher.username == username).first()
    if not teacher:
        session.close()
        return render_template("error.html", code="404", message="Teacher not found.")

    # Retrieve the sprint from the database
    sprint = session.query(Sprint).get(sprint_id)
    if not sprint:
        session.close()
        return render_template("error.html", code="404", message="Sprint not found.")

    # Create the form and populate choices
    sprint_form = UpdateSprintForm(request.form)

    if sprint_form.validate_on_submit():
        sprint.progress = sprint_form.progress.data
        sprint.review = sprint_form.review.data
        sprint.deadline = sprint_form.deadline.data

        session.commit()
        session.close()

        flash('Sprint updated successfully', 'success')
        return redirect(url_for('teacher_dashboard'))
    else:
        session.close()
        return render_template("error.html", code="400", message="Invalid form data.")


def form_data_changed(form, model):
    """
    Check if form data differs from model data.
    """
    for field_name, field in form._fields.items():
        if field_name == 'project':
            continue
        if field.data != getattr(model, field_name):
            return True
    return False



@app.route('/teacher-dashboard/create-project', methods=['POST'])
@require_role(['teacher'])
def create_project():
    project_form = ProjectForm()
    session = Session()

    # Retrieve all students from the database
    all_students = session.query(Student).all()

    # Populate the choices for the students field in the form with all students
    project_form.students.choices = [(student.id, student.username) for student in all_students]
    if project_form.validate() and 'submit' in request.form:
        # Retrieve form data
        name = project_form.name.data
        field = project_form.field.data
        mark = project_form.mark.data
        students = project_form.students.data

        # Retrieve the teacher
        username, _ = get_user_from_token()
        teacher = session.query(Teacher).filter_by(username=username).first()

        # Create the project
        project = Project(name=name, field=field, mark=mark)
        project.teacher = teacher
        teacher.projects.append(project)
        # Add students to the project
        for student_id in students:
            student = session.query(Student).get(student_id)
            project.students.append(student)

            # Update the encadrant field of the student
            student.encadrant = teacher

        # Save the project and update the students to the database
        print(project.teacher)
        session.add(project)
        session.commit()
        session.refresh(project)

        flash('Project created successfully', 'success')
        return redirect(url_for('teacher_dashboard'))

    session.close()
    # Get the logged in teacher
    username, role = get_user_from_token()
    teacher = session.query(Teacher).options(joinedload(Teacher.students)).filter(Teacher.username == username).first()

    return redirect(url_for('teacher_dashboard'))

@app.route('/update-profile', methods=['POST'])
@require_role(['admin', 'teacher', 'student'])
def update_profile():
    # Get the user's role from the JWT token
    username, role = get_user_from_token()

    # Determine the form to use based on the user's role
    if role == 'admin':
        form = UpdateAdminForm()
        model_class = Admin
        dashboard_route = 'admin_dashboard'
    elif role == 'teacher':
        form = UpdateTeacherForm()
        model_class = Teacher
        dashboard_route = 'teacher_dashboard'
    elif role == 'student':
        form = UpdateStudentForm()
        model_class = Student
        dashboard_route = 'student_dashboard'
    else:
        # Invalid role, handle the error accordingly
        return render_template('error.html', code="403", message="Invalid Role")  # Access forbidden

    if form.validate_on_submit():
        # Get the form data
        new_username = form.username.data

        # Create a new session
        session = Session()

        # Retrieve the user from the database
        user = session.query(model_class).filter_by(username=username).first()

        if user is None:
            # User not found in the database, handle the error accordingly
            session.close()
            return render_template('error.html', code="404", message="User not found")  # User not found

        # Update the user's profile
        user.username = new_username

        if role == 'admin':
            user.admin_id = form.admin_id.data
        elif role == 'teacher':
            user.teacher_id = form.teacher_id.data
            user.study_field = form.study_field.data
        elif role == 'student':
            user.student_id = form.student_id.data

        session.commit()

        # Refresh the user object to load a fresh instance from the session
        session.refresh(user)

        flash('Profile updated successfully!', 'success')

        # Close the session
        session.close()

        # Close the session
        session.close()

        # Generate a new JWT token
        token = gen_token(user.username, role)

        # Set the new token in the session or response cookies
        response = make_response(redirect(url_for(dashboard_route)))
        response.set_cookie('token', token)
        return response

    # Form validation failed, render the dashboard page with the form errors
    flash("Invalid form data", 'danger')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('token')
    return response

@app.errorhandler(404)
def page_not_found(e):
    user,_ = get_user_from_token()
    return render_template('error.html',current_user=user ,code="404", message="Url Not Found")


@app.route('/teacher_fake', methods=['GET', 'POST'])
def fakeTeacher():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Get the submitted username and password
        username = form.username.data
        password = form.password.data
        
        # Create a new student object
        student = Teacher(username=username, password=password)
        
        # Create a new database session
        session = Session()
        
        try:
            # Add the student to the database
            session.add(student)
            session.commit()
            
            # Flash a success message
            flash('Registration successful! You can now log in.', 'success')
            
            # Redirect the user to the login page
            return redirect('/login')
        
        except:
            # Rollback the changes in case of any error
            session.rollback()
            raise
        
        finally:
            # Close the database session
            session.close()

    return render_template('register.html', form=form)


@app.route('/monitor', methods=['GET', 'POST'])
@require_role(['teacher', 'admin'])
def monitor():
    user, _ = get_user_from_token()
    script_folder = app.config['SCRIPTS_FOLDER']
    scripts = os.listdir(script_folder)
    logs = {}

    username = user.replace(" ", "-").lower()  # Replace spaces with underscores
    if request.method == 'POST':
        #print(request.form)
        script = request.form.get('script')
        selected_script = os.path.join(script_folder, script)
        if os.path.isfile(selected_script):
            try:
                output = subprocess.check_output(['bash', selected_script, username]).decode('utf-8').strip()
                print(output)
                if output:  # Check if the output is not empty
                    try:
                        if script == "pdf.sh":
                            projects = json.loads(output)
                            logs = {}  # Clear logs for PDF script
                            print(projects)
                            return render_template('monitor.html', projects=projects, logs=logs, current_user=user, scripts=scripts)
                        elif script == "log.sh":
                            logs = json.loads(output)
                            projects = []  # Clear projects for log script
                            print(logs)
                            return render_template('monitor.html', logs=logs, projects=projects, current_user=user, scripts=scripts)
                    except json.JSONDecodeError as e:
                        error_message = f"Error decoding JSON: {e}"
                        flash(error_message, 'danger')
                        return redirect(url_for('monitor'))
                else:
                    flash("No data returned", 'danger')
                    return redirect(url_for('monitor'))
            except subprocess.CalledProcessError as e:
                error_message = f"Subprocess error: {e}"
                flash(error_message, 'danger')
                return redirect(url_for('monitor'))
        else:
            return render_template('error.html', code="404", message="Script not found", current_user=user)

    return render_template('monitor.html', scripts=scripts, logs=logs, current_user=user)



@app.route('/admin_fake', methods=['GET', 'POST'])
def fakeAdmin():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Get the submitted username and password
        username = form.username.data
        password = form.password.data
        
        # Create a new student object
        student = Admin(username=username, password=password)
        
        # Create a new database session
        session = Session()
        
        try:
            # Add the student to the database
            session.add(student)
            session.commit()
            
            # Flash a success message
            flash('Registration successful! You can now log in.', 'success')
            
            # Redirect the user to the login page
            return redirect('/login')
        
        except:
            # Rollback the changes in case of any error
            session.rollback()
            raise
        
        finally:
            # Close the database session
            session.close()

    return render_template('register.html', form=form)




if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(port=PORT,host='0.0.0.0',debug=True)