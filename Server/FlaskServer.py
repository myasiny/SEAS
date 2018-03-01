# -*- coding:UTF-8 -*-

from flask import Flask, request, jsonify
from Models import MySQLdb, Password, Credential, Question, Exam
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import json
import datetime

app = Flask(__name__)
db = MySQLdb("TestDB", app)
app.config["DEBUG"] = True
app.config["JWT_SECRET_KEY"] = "CHANGE THIS BEFORE DEPLOYMENT ! ! !"
if app.config["DEBUG"]:
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
else:
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=18)

jwt = JWTManager(app)

def check_auth(token, *allowed_roles):
    user, role, token_time = token
    return role in allowed_roles

@app.route("/")
def test_connection():
    return jsonify("I am alive!")


@app.route("/organizations", methods=["PUT"])
@jwt_required
def signUpOrganization():
    if check_auth(get_jwt_identity(), "superuser"):
        return jsonify(db.initialize_organization(request.form["data"]))
    else:
        return jsonify("Unauthorized access!")


@app.route("/organizations/<string:organization>", methods = ["PUT"])
@jwt_required
def signUpUser(organization):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin"):
        return jsonify("Unauthorized access!")
    else:
        passwd = Password().hashPassword(request.form["Password"])
        username = request.form["Username"]
        role = request.form["Role"].lower()
        command = "Insert into %s.members(PersonID, Role, Name, Surname, Username, Password, Email, Department) " \
                  "values(%s, '%d', '%s', '%s', '%s', '%s', '%s', '%s')" \
                  % (organization,
                     request.form["ID"],
                     int(db.execute("SELECT RoleID FROM %s.roles WHERE Role = '%s'" % (
                     organization, role))[0][0]),
                     request.form["Name"],
                     request.form["Surname"],
                     username,
                     passwd,
                     request.form["Email"],
                     request.form["Department"]
                     )

        rtn = jsonify(db.execute(command))
        return rtn


@app.route("/organizations/<string:organization>/<string:username>", methods=["GET"])
def signInUser(organization, username):
    organization = organization.replace(" ", "_").lower()
    username = request.authorization["username"]
    try:
        passwd = db.execute("select Password from %s.members where Username = '%s'"
                            % (organization, username))[0][0]
        if Password().verify_password_hash(request.authorization["password"], passwd):
            rtn = list(db.execute("select Username, Name, Surname, PersonID, Role, Email, Department "
                                  "from %s.members where Username=('%s')" % (organization, username))[0])
            rtn[4] = db.execute("SELECT Role FROM %s.roles WHERE RoleID = '%s'" % (organization, rtn[4]))[0][0]
            rtn.append(organization)
            token = create_access_token(identity=(rtn[0], rtn[4], str(datetime.datetime.today())))
            rtn.append(token)
            return jsonify(rtn)

        else:
            return jsonify("Wrong Password")
    except IndexError:
        return jsonify("Wrong Username")


@app.route("/organizations/<string:organization>/<string:username>/out", methods=["GET", "PUT"])
def signOutUser(organization, username):
    pass

@app.route("/organizations/<string:organization>/<string:course>", methods=['PUT'])
@jwt_required
def addCourse(organization, course):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin"):
        return jsonify("Unauthorized access!")
    else:
        name = request.form["name"]
        code = request.form["code"]
        lecturers = request.form["lecturers"]
        return jsonify(db.add_course(organization, name, code, lecturers))


@app.route("/organizations/<string:organization>/<string:course>/get", methods=['GET'])
@jwt_required
def getCourse(organization, course):
    return jsonify(db.get_course(organization, course))


@app.route("/organizations/<string:organization>/<string:course>/register/<string:liste>", methods=['PUT'])
@jwt_required
def putStudentList(organization, course, liste):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin", "lecturer"):
        return jsonify("Unauthorized access!")

    else:
        return jsonify(db.registerStudentCSV(request.files["liste"], organization, course, request.form["username"]))


@app.route("/organizations/<string:organization>/<string:course>/register", methods=['GET'])
@jwt_required
def getStudentList(organization, course):
    token = get_jwt_identity()
    return jsonify(db.get_course_participants(course, organization))


@app.route("/organizations/<string:organization>/<string:username>/courses/role=lecturer", methods=["GET"])
@jwt_required
def getLecturerCourseList(organization, username):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin", "lecturer"):
        return jsonify("Unauthorized access!")
    else:
        return jsonify(db.get_lecturer_courses(organization, username))


@app.route("/organizations/<string:organization>/<string:course>/delete_user", methods=['DELETE'])
@jwt_required
def deleteStudentFromLecture(organization, course):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin", "lecturer"):
        return jsonify("Unauthorized access!")
    else:
        return jsonify(db.delete_student_course(organization, course, request.form["Student"]))


@app.route("/organizations/<string:organization>/<string:username>/edit_password", methods=["PUT"])
@jwt_required
def changePassword(organization, username):
    ismail = request.form["isMail"]
    if ismail == "True":
        ismail = True
    else:
        ismail = False
    return jsonify(db.changePasswordOREmail(organization, username, request.form["Password"], request.form["newPassword"], email=ismail))


@app.route("/organizations/<string:organization>/<string:course>/exams/add", methods=["PUT"])
@jwt_required
def addExam(organization, course):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin", "lecturer"):
        return jsonify("Unauthorized access!")
    else:
        name = request.form["name"]
        time = request.form["time"]
        duration = request.form["duration"]
        questions = json.loads(request.form["questions"])
        exam = Exam(name, course, time, duration, organization)
        for j in questions:
            i=questions[j]
            exam.addQuestion(
                i["type"],
                i["subject"],
                i["text"],
                i["answer"],
                i["inputs"],
                i["outputs"],
                i["value"],
                i["tags"])
        return jsonify(exam.save(db))


# todo: fatihgulmez
@app.route("/organizations/<string:organization>/<string:course>/exams/", methods=["GET"])
@jwt_required
def getExamsOfLecture(organization, course):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin", "lecturer"):
        return jsonify("Unauthorized access!")
    else:
        return jsonify("Constraction Sİte!")
    pass


@app.route("/organizations/<string:organization>/<string:course>/exams/<string:name>", methods=["GET"])
@jwt_required
def getExam(organization, course, name):
    exam = Exam(name, course, None, None, organization)
    return jsonify(exam.get(db))


@app.route("/organizations/<string:organization>/<string:course>/exams/<string:name>/addQuestion", methods=["PUT"])
@jwt_required
def addQuestionsToExam(organization, course, name):
    token = get_jwt_identity()
    if not check_auth(token, "superuser", "admin", "lecturer"):
        return jsonify("Unauthorized access!")
    else:
        return jsonify("Constraction Sİte!")
    pass


@app.route("/organizations/<string:organization>/<string:course>/exams/<string:name>/answers/<string:username>", methods=["PUT"])
@jwt_required
def answerExam(organization, course, name, username):
    return jsonify(db.add_answer(organization, name, username, request.form["answers"]))


if __name__ == "__main__":
    app.run(host="10.50.81.24", port=8888, threaded = True)