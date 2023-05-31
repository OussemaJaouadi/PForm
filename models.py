from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

project_student_association = Table(
    'project_student_association', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('student_id', Integer, ForeignKey('students.id'))
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(50))
    role = Column(String(20), default='student')

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }

    def __init__(self, username=None, password=None):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        """Set the password for the user."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password, password)


class Request(Base):
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'))

    sender = relationship('User', backref='sent_requests', foreign_keys=[sender_id])
    admin = relationship('Admin', back_populates='received_requests', foreign_keys=[admin_id])

    def __repr__(self):
        return f"Request(id={self.id}, content='{self.content}', sender_id={self.sender_id}, admin_id={self.admin_id})"


class Admin(User):
    __tablename__ = 'admins'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    admin_id = Column(String(20))

    received_requests = relationship("Request", back_populates="admin")

    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }


class Student(User):
    __tablename__ = 'students'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    student_id = Column(String(20))

    encadrant_id = Column(Integer, ForeignKey('teachers.id'))
    encadrant = relationship("Teacher", back_populates="students", foreign_keys=[encadrant_id])

    projects = relationship("Project", secondary=project_student_association, back_populates="students")

    __mapper_args__ = {
        'polymorphic_identity': 'student'
    }

    def __init__(self, username=None, password=None, student_id=None, encadrant_id=None):
        super().__init__(username, password)
        self.student_id = student_id
        self.encadrant_id = encadrant_id


class Teacher(User):
    __tablename__ = 'teachers'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    teacher_id = Column(String(20))
    study_field = Column(String(50))

    students = relationship("Student", back_populates="encadrant", foreign_keys=[Student.encadrant_id])

    projects = relationship("Project", back_populates="teacher")

    __mapper_args__ = {
        'polymorphic_identity': 'teacher'
    }

    def __init__(self, username=None, password=None, teacher_id=None, study_field=None):
        super().__init__(username, password)
        self.teacher_id = teacher_id
        self.study_field = study_field



class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    field = Column(String(50))
    rapport = Column(String(100))  # Assuming file path or URL to PDF file
    mark = Column(Integer)

    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    teacher = relationship("Teacher", back_populates="projects")

    students = relationship("Student", secondary=project_student_association, back_populates="projects")
    sprint_entries = relationship("Sprint", back_populates="project")


class Sprint(Base):
    __tablename__ = 'sprints'

    id = Column(Integer, primary_key=True)
    sprint_number = Column(Integer)
    sprint_name = Column(String(50))
    progress = Column(String(20))
    review = Column(String(20))
    start_date = Column(DateTime)
    deadline = Column(DateTime)

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", back_populates="sprint_entries")
