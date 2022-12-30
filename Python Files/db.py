from dis import Instruction
from flask_sqlalchemy import SQLAlchemy
import datetime
import hashlib
import os

import bcrypt
db = SQLAlchemy()

# your classes here
#table associating students with events
association_table_student = db.Table("associationS", db.Model.metadata,
    db.Column("event_id", db.Integer, db.ForeignKey("event.id")),
    db.Column("student_id", db.Integer, db.ForeignKey("student.id"))
)


class Event(db.Model):
    """
    Sets variables for event class
    """
    _tablename_ = "course"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    hostName = db.Column(db.String,nullable=False)
    title = db.Column(db.String,nullable=False)
    description = db.Column(db.String,nullable=False)
    time = db.Column(db.String,nullable=False)
    location = db.Column(db.String,nullable=False)
    students = db.relationship("Student", secondary=association_table_student, back_populates="events")

    def __init__(self, **kwargs):
        self.hostName = kwargs.get("hostName", "")
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.time = kwargs.get("time", "")
        self.location = kwargs.get("location", "")

    def serialize(self):
        """
        Makes function readable
        """
        return{
            "id":self.id,
            "hostName":self.hostName,
            "title":self.title,
            "description":self.description,
            "time":self.time,
            "location":self.location,
            "students":[st.SSerialize() for st in self.students]
        }
    
    def SSerialize(self):
        """
        Simple Serialize function to prevent the function infinitely looping
        """
        return{
            "id":self.id,
            "hostName":self.hostName,
            "title":self.title,
            "description":self.description,
            "time":self.time,
            "location":self.location
        }

class Student(db.Model):
    """
    Sets variables for student class
    """
    _tablename_ = "student"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    name = db.Column(db.String,nullable=False)
    netid = db.Column(db.String,nullable=False)
    major = db.Column(db.String,nullable=False)
    grade = db.Column(db.String,nullable=False)
    events = db.relationship("Event", secondary=association_table_student, back_populates="students")  
    user = db.relationship("User", cascade = "delete")

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.netid = kwargs.get("netid", "")
        self.major = kwargs.get("major", "")
        self.grade = kwargs.get("grade", "")

    def serialize(self):
        return{
            "id":self.id,
            "name":self.name,
            "netid":self.netid,
            "major":self.major,
            "grade":self.grade,
            "events":[i.SSerialize() for i in self.events],
        }
    
    def SSerialize(self):
        """
        Simple Serialize function to prevent the function infinitely looping
        """
        return{
            "id":self.id,
            "name":self.name,
            "netid":self.netid,
            "major":self.major,
            "grade":self.grade
        }

    def getUser(self):
        """"
        provides user
        """
        return{
            "user":self.user
        }

class User(db.Model):
    """
    User model
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)

    # User information
    email = db.Column(db.String, nullable=False, unique=True)
    password_digest = db.Column(db.String, nullable=False)

    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)

    student_id = db.Column(db.Integer,db.ForeignKey("student.id"),nullable=True)

    def __init__(self, **kwargs):
        """
        Initializes a User object
        """
        self.email = kwargs.get("email")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()

    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        """
        Renews the sessions, i.e.
        1. Creates a new session token
        2. Sets the expiration time of the session to be a day from now
        3. Creates a new update token
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a user
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token

