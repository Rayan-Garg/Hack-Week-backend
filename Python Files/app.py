from db import db
from db import Event
from db import Student
from flask import Flask
from flask import request
import json
import users_dao
import datetime

app = Flask(__name__)
db_filename = "cms.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    return json.dumps(data), code

def failure_response(message, code=404):
    return json.dumps({"error": message}), code

#dummy data the frontend team needed
event = [
    {
        "hostName": "Cornell",
        "title": "Slope Day",
        "description": "Best day of the year",
        "time": "05/12/2022 12:30",
        "location": "Slope",
    },
    {
        "hostName": "Movie Club",
        "title": "Self Care",
        "description": "a chance to watch a movie and relax with friends",
        "time": "10/23/2022 15:30",
        "location": "Latino Living Center",
    },
    {
        "hostName": "Movie Club",
        "title": "breakfast",
        "description": "Eat a relaxing meal",
        "time": "10/23/2022 10:00",
        "location": "Willard Straight Hall",
    },
    {
        "hostName": "Movie Club",
        "title": "All White Party",
        "description": "a party with an all white dress theme",
        "time": "10/23/2022 20:00",
        "location": "Appel",
    }
]
with app.app_context():
    if(Event.query.filter_by(title="All White Party").first()) is None:
        new_event = Event(hostName="Movie Club",title="All White Party",description="a party with an all white dress theme",time="10/23/2022 20:00",location="Appel")
        db.session.add(new_event)
        db.session.commit()
    if(Event.query.filter_by(title="Slope Day").first()) is None:
        event2 = Event(hostName=event[0]["hostName"],title=event[0]["title"],description=event[0]["description"],time=event[0]["time"],location=event[0]["location"])
        db.session.add(event2)
        db.session.commit()
    if(Event.query.filter_by(title="Self Care").first()) is None:
        event3 = Event(hostName=event[1]["hostName"],title=event[1]["title"],description=event[1]["description"],time=event[1]["time"],location=event[1]["location"])
        db.session.add(event3)
        db.session.commit()
    if(Event.query.filter_by(title="breakfast").first()) is None:
        event4 = Event(hostName=event[2]["hostName"],title=event[2]["title"],description=event[2]["description"],time=event[2]["time"],location=event[2]["location"])
        db.session.add(event4)
        db.session.commit()

def extract_token(request):
    """
    Helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None: 
        return False, failure_response("Missing authorization header",400)
    bearer_token = auth_header.replace("Bearer","").strip()
    if bearer_token is None or not bearer_token:
        return False, failure_response("Invalid authorization header")
    
    return True, bearer_token

# your routes here
@app.route("/")
@app.route("/api/events/")
def get_courses():
    """
    Gets all events
    """
    return success_response ({"events": [e.serialize() for e in Event.query.all()]})

@app.route("/api/events/", methods=["POST"])
def create_event():
    """
    Creates an event
    """
    body = json.loads(request.data)
    club = body.get("hostName")
    name = body.get("title")
    description = body.get("description")
    time = body.get("time")
    location = body.get("location")
    if body is None or club is None or name is None or description is None or time is None or location is None:
        return failure_response("Full event information not provided. An event needs a body, hostName, title, description, time, and location.",400)
    new_event = Event(hostName=club,title=name,description=description,time=time,location=location)
    db.session.add(new_event)
    db.session.commit()
    return success_response (new_event.serialize(), 201)

@app.route("/api/events/<string:time>/")
def get_event(time):
    """
    Gets an event by the date
    """
    event = Event.query.filter_by(time=time).first()
    if event is None:
        return failure_response("Course not found!")
    return success_response(event.serialize())

@app.route("/api/students/", methods=["POST"])
def create_student():
    """
    Create a student
    """
    body = json.loads(request.data)
    name = body.get("name")
    netid = body.get("netid")
    major = body.get("major")
    grade = body.get("grade")
    if name is None or netid is None or major is None or grade is None:
        return failure_response("Full student information not provided. Need a name, netid, major, and grade.",400)
    new_student = Student(name=name,netid=netid,major=major,grade=grade)
    db.session.add(new_student)
    db.session.commit()
    return success_response (new_student.serialize(), 201)

@app.route("/api/student/<string:name>/", methods=["DELETE"])
def delete_student(name):
    """
    Deletes a student by its name
    """
    student = Student.query.filter_by(name=name).first()
    if student is None:
        return failure_response("Student not found!")
    db.session.delete(student)
    db.session.commit()
    return success_response(student.serialize())

@app.route("/api/event/<int:id>/", methods=["DELETE"])
def delete_event(id):
    """
    Deletes an event by its id
    """
    event = Event.query.filter_by(id=id).first()
    if event is None:
        return failure_response("Event not found!")
    db.session.delete(event)
    db.session.commit()
    return success_response(event.serialize())

@app.route("/register/", methods=["POST"])
def register_account():
    """
    Endpoint for registering a new user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")
    studentid = body.get("studentid")

    if studentid is None or password is None or email is None:
        return failure_response("Missing information")

    student = Student.query.filter_by(id=studentid).first()
    if student is None:
        return failure_response("No student corresponding to given id")
    if student.user:
        return failure_response("Student already has an id and password")
        
    success,user = users_dao.create_user(email,password,studentid)
    if not success:
        return failure_response("User exists",400)

    return success_response(
        {
            "session_token":user.session_token,
            "session_expiration":str(user.session_expiration),
            "update_token":user.update_token
        }
    )


@app.route("/login/", methods=["POST"])
def login():
    """
    Endpoint for logging in a user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return failure_response("Missing email or password",400)

    success, user = users_dao.verify_credentials(email,password)

    if not success:
        return failure_response("Incorrect email or password",401)

    return success_response({
        "session_token":user.session_token,
        "session_expiration":str(user.session_expiration),
        "update_token":user.update_token
    })

@app.route("/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updating a user's session
    """
    success, update_token = extract_token(request)
    if not success:
        return failure_response("Could not extract update token", 400)
    success_user, user = users_dao.renew_session(update_token)

    if not success_user:
        return failure_response("Invalid update token",400)

    return success_response({
        "session_token":user.session_token,
        "session_expiration":str(user.session_expiration),
        "update token": user.update_token
    })


@app.route("/secret/", methods=["GET"])
def secret_message():
    """
    Endpoint for verifying a session token and returning a secret message

    In your project, you will use the same logic for any endpoint that needs 
    authentication
    """
    success, session_token = extract_token(request)
    if not success:
        return failure_response("Session token invalid",400)
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token",400)
    return success_response({"message":"You have successfully implemented sessions!"})

@app.route("/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging out a user
    """
    success, session_token = extract_token(request)
    if not success:
        return failure_response("Could not extract session token", 400)
    
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token",400)
    
    user.session_token = ""
    user.session_expiration = datetime.datetime.now()
    user.update_token = ""
    
    return success_response({"message":"You have successfully logged out!"})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)