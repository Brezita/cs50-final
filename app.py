import os
from cs50 import SQL
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session

from helpers import login_required

db = SQL("sqlite:///stitchbook.db")
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

# Ensure templates are auto-reloaded - taken from Finance files
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
Session(app)

def allowed_file(filename):
    '''Check file extension against list of allowed file extensions'''
    print("Checking if file extension allowed")
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(file):
    '''Takes image from form and uploads it'''
    print("Extension allowed, initiating file upload")
    if file and allowed_file(file.filename):
        print("File allowed")
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print('upload_image filename: ' + filename)
        # return redirect(url_for('uploaded_file', filename=filename))
        # Return filename to the main app
        return filename

@app.route("/login", methods=["GET", "POST"])
def login():
    # Display login page via get; log user in via post
    # Forget any user_id
    session.clear()

    if request.method == "GET":
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # TO DO
    return render_template("register.html")


@app.route("/")
# @login_required
def index():
    projects = db.execute("SELECT project.id, project.name, current.image, current.timestamp FROM project \
        JOIN current ON project.id = current.project_id ORDER BY current.timestamp DESC LIMIT 10")
    # WHERE project_id IN (SELECT project_id FROM bridge WHERE user_id = :user_id)", user_id=
    # TO DO: edit this once profile section is in place
    print(f"{projects}")
    projectno = len(projects)
    return render_template("index.html", projects=projects, projectno=projectno)


@app.route("/add", methods=["GET", "POST"])
# @login_required
def add():
    if request.method == "GET":
        cats = db.execute("SELECT DISTINCT tag FROM tags")
        # Don't forget to change this to be tags that are associated with the user
        categories = len(cats)
        return render_template("add_project.html", categories=categories, cats=cats)
    else:
        print("Initiating form entry")
        formdata = request.form.to_dict()

        # Check whether all the information is available to calculate the size, then do so
        # TO DO: replace the "metric" variable with some proper code
        metric = "in"
        # Overtwo value set to False by default
        overtwo = False
        if '' not in (formdata['count'], formdata['width'], formdata['height']):
            if not request.form.get("overtwo"):
                threadcount = float(formdata['count'])
            else:
                threadcount = float(formdata['count']) / 2
                overtwo = True

            # Calculate the size of the project
            height = float(formdata['height']) / threadcount
            width = float(formdata['width']) / threadcount

            # TO-DO: add rounding function to 2 decimal places
            size = str(round(height, 2)) + metric + " x "+ str(round(width, 2)) + metric
        else:
            size = None


        # Extract the status of the project:
        if not request.form.get("queue") and not request.form.get("finished"):
            status = "Started"
        elif not request.form.get("queue"):
            status = "Finished"
        else:
            status = "Queued"

        # Insert into database and return project_id
        db.execute("INSERT INTO project (name, designer, magazine, issue, startdate, finishdate, \
            height, width, size, status, priority, deadline) VALUES (:name, :designer, :magazine, \
            :issue, :startdate, :finishdate, :height, :width, :size, :status, :priority, \
            :deadline)", name=formdata['projectname'], designer=formdata['designer'], \
            magazine=formdata['whichmag'], issue=formdata['issue'], startdate=formdata['start'], \
            finishdate=formdata['finish'], height=formdata['height'], width=formdata['width'], \
            size=size, status=status, priority=formdata['priority'], deadline=formdata['deadline'])
        lastid = db.execute("SELECT last_insert_rowid()")
        lastid = lastid[0]['last_insert_rowid()']

        filename = None
        # Insert deets into current - if there are any
        if request.files['addimage'] is not None:
            file = request.files['addimage']
            if file.filename != '':
                print("File found")
                filename = upload_image(file)
                print(f"Returned {filename}")
        else:
            print("No file included")
        

        print(f"Inserting {filename}")
        db.execute("INSERT INTO current (project_id, image, notes) VALUES (:project_id, \
                :image, :notes)", project_id=lastid, image=filename, notes=formdata['notes'])

        keys = list(formdata.keys())

        # Check whether kit box ticked - if not, get thread and fabric
        if request.form.get("kit") is None:

            # Separate the list of threads out into a list of string, then enter into the database
            if formdata['threads'] != '':
                threadlist = formdata['threads'].split(",")
                for thread in range(len(threadlist)):
                    db.execute("INSERT INTO thread (project_id, thread_no) VALUES (:project_id, \
                        :thread_no)", project_id=lastid, thread_no=thread)

            # Insert deets into handdye, if there are any
            dyerlist = []
            numberlist = []
            typelist = []

            for key in range(len(keys)):
                if "threaddyer" in keys[key]:
                    dyerlist.append(formdata[keys[key]])
                elif "flossnumber" in keys[key]:
                    numberlist.append(formdata[keys[key]])
                elif "threadtype" in keys[key]:
                    typelist.append(formdata[keys[key]])


            iterations = len(dyerlist)
            if iterations != 0 and (dyerlist[0] or numberlist[0] or typelist[0]) is not None:
                for iterate in range(iterations):
                    db.execute("INSERT INTO handdye (project_id, nameno, type, dyer) VALUES \
                        (:project_id, :nameno, :threadtype, :dyer)", project_id=lastid, \
                        nameno=numberlist[iterate], threadtype=typelist[iterate], \
                        dyer=dyerlist[iterate])


            # Insert deets into fabric - if there are any
            db.execute("INSERT INTO fabric (project_id, dyer, count, colour, type, overtwo) \
                VALUES (:project_id, :dyer, :count, :colour, :fabtype, :overtwo)", \
                project_id=lastid, dyer=formdata['dyer'], count=formdata['count'], \
                colour=formdata['colour'], fabtype=formdata['type'], overtwo=overtwo)

        catlist = []
        eventlist = []

        # Insert categories and events into tags
        for key in range(len(keys)):
            if ("catcheck" or "newcat") in keys[key]:
                catlist.append(formdata[keys[key]])
            elif "event" in keys[key]:
                eventlist.append(formdata[keys[key]])


        iterations = len(catlist)
        if iterations != 0 and catlist[0] is not None:
            for iterate in range(iterations):
                db.execute("INSERT INTO tags (project_id, tag, event_tag) VALUES \
                    (:project_id, :tag, 'FALSE')", project_id=lastid, tag=catlist[iterate])


        iterations = len(eventlist)
        if iterations != 0 and eventlist[0] is not None:
            for iterate in range(iterations):
                db.execute("INSERT INTO tags (project_id, tag, event_tag) VALUES (:project_id, \
                    :tag, 'TRUE')", project_id=lastid, tag=eventlist[iterate])


        return redirect("/")


@app.route("/all")
# @login_required
def all():
    # TO DO - add userid
    projects = db.execute("SELECT project.id, project.name, project.designer, current.image FROM project JOIN \
        current ON project.id = current.project_id")
    projectno = len(projects)
    return render_template("projects.html", projects=projects, projectno=projectno, status="All")


@app.route("/current")
# @login_required
def current():
    print("Directing to current")
    # TO DO  - add userid
    projects = db.execute("SELECT project.id, project.name, project.designer, current.image FROM project JOIN current ON project.id = current.project_id WHERE status = 'Started'")
    projectno = len(projects)
    return render_template("projects.html", projects=projects, projectno=projectno, status="Current")


@app.route("/finished")
def finished():
    # TO DO - add userid
    projects = db.execute("SELECT project.id, project.name, project.designer, current.image FROM project JOIN \
        current ON project.id = current.project_id WHERE status = 'Finished'")
    projectno = len(projects)
    return render_template("projects.html", projects=projects, projectno=projectno, status="Finished")


@app.route("/queued")
def queued():
    # TO DO - add userid
    projects = db.execute("SELECT project.id, project.name, project.designer, current.image FROM project JOIN \
        current ON project.id = current.project_id WHERE status = 'Queued'")
    projectno = len(projects)
    return render_template("projects.html", projects=projects, projectno=projectno, status="Queued")


@app.route("/view", methods=["POST"])
# @login_required
def view(id=None):
    # TO DO - add userid once added
    if id == None:
        id = request.form.get("id")

    project = db.execute("SELECT * FROM project \
        LEFT JOIN current ON project.id = current.project_id \
        LEFT JOIN fabric ON project.id = fabric.project_id \
        WHERE id = :id", id=id)
    project = project[0]

    thread = db.execute("SELECT * FROM thread WHERE project_id = :id", id=id)

    handdye = db.execute("SELECT * FROM handdye WHERE project_id = :id", id=id)

    tags = db.execute("SELECT tag FROM tags WHERE project_id = :id", id=id)
    print(f"{tags}" )
    print(f"{project}")
    print(f"{thread}")
    print(f"{handdye}")
    return render_template("view.html", project=project, thread=thread, handdye=handdye, tags=tags)

# Route to the update page
@app.route("/update", methods=["POST"])
# @login_required
def update():
    # TO DO: add user id aspect to SQL query
    id = request.form.get("id")

    project = db.execute("SELECT name, status FROM project WHERE id = :id", id=id)
    project = project[0]['name']

    categories = db.execute("SELECT * FROM tags WHERE project_id = :id", id=id)

    return render_template("update.html", project=project, categories=categories)

# Actually update server then reroute back to the view page
@app.route("/updatedb", methods=["POST"])
# @login_required
def updatedb():
    formdata = request.form.to_dict()
    id = formdata['id']

    # Extract the status of the project:
    if not request.form.get("queue") and not request.form.get("finished"):
        status = "Started"
    elif not request.form.get("queue"):
        status = "Finished"
    else:
        status = "Queued"

    filename = None
    # Insert deets into current - if there are any
    if request.files['addimage'] is not None:
        file = request.files['addimage']
        if file.filename != '':
            print("File found")
            filename = upload_image(file)
            print(f"Returned {filename}")
    else:
        print("No file included")
    

    print(f"Inserting {filename}")
    db.execute("INSERT INTO current (project_id, image, notes) VALUES (:project_id, \
            :image, :notes)", project_id=lastid, image=filename, notes=formdata['notes'])

    keys = list(formdata.keys())

    catlist = []
    eventlist = []

    # Insert categories and events into tags
    for key in range(len(keys)):
        if ("catcheck" or "newcat") in keys[key]:
            catlist.append(formdata[keys[key]])
        elif "event" in keys[key]:
            eventlist.append(formdata[keys[key]])


    iterations = len(catlist)
    if iterations != 0 and catlist[0] is not None:
        for iterate in range(iterations):
            db.execute("INSERT INTO tags (project_id, tag, event_tag) VALUES \
                (:project_id, :tag, 'FALSE')", project_id=lastid, tag=catlist[iterate])


    iterations = len(eventlist)
    if iterations != 0 and eventlist[0] is not None:
        for iterate in range(iterations):
            db.execute("INSERT INTO tags (project_id, tag, event_tag) VALUES (:project_id, \
                :tag, 'TRUE')", project_id=lastid, tag=eventlist[iterate])


    return redirect("/view", id=id)

@app.route("/delete", methods=["POST"])
# @login_required
def delete():
    id = request.form.get("id")

    #db.execute("DELETE FROM project \ LEFT JOIN...")

    return redirect("/")

@app.route("/calculator")
# @login_required
def calculator():
    return render_template("calculator.html")


@app.route("/about")
def about():
    # TO DO
    return render_template("about.html")


@app.route("/profile")
# @login_required
def profile():
    return render_template("profile.html")