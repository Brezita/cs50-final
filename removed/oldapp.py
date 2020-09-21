# Renders the edit page when the user passes project information in
@app.route("/edit", methods=["POST"])
# @login_required
def edit():
    # TO DO: rework this section so that it pulls information from threads+handdyes OR fabrics OR project depending on input
    # also rework the edit page and view page to reflect this
    id = request.form.get("id")

    project = db.execute("SELECT * FROM project WHERE id = :id", id=id)
    project = project[0]
    print(f"{project}")

    fabric = db.execute("SELECT * FROM fabric WHERE project_id = :id", id=id)
    fabric = fabric[0]
    print(f"{fabric}")

    thread = db.execute("SELECT thread_no FROM thread WHERE project_id = :id", id=id)
    print(f"{thread}")

    handdye = db.execute("SELECT nameno, type, dyer FROM handdye WHERE project_id = :id", id=id)
    print(f"{handdye}")
    return render_template("edit_project.html", project=project, fabric=fabric, thread=thread, handdye=handdye)

# Passes the amended information to the server
@app.route("/editproject", methods=["POST"])
# @login_required
def editproject():
    # Get project id
    id = formdata['id']

    # Determine which fields have been changed
    changed = request.form.get("datapasser")
    print(f"Changes: {changed}")

    # Turn changes variable into list
    changed = changed.split(",")

    # Extract all data from form
    formdata = request.form.to_dict()
    print(f"Formdata: {formdata}")

    # If key in changes, move value into separate array
    changes = []
    for change in changed:
        changes.append(formdata[changed[change]])

    # Insert data into db using changes as column and 
    for change in changed:
        if formdata[keys[key]] != '':
            db.execute("UPDATE project SET :column VALUE :value WHERE id = :id", column=changed[change], value=formdata[change[changed]], id=id)
    
    # TO DO - will need to update size if height/width change; and change field names
    # to match database column names

    return redirect("/")

@app.route("/editthreads", methods=["POST"])
# @login_required
def editthreads():
    return redirect("/")

@app.route("/editfabric", methods=["POST"])
def editfabric():
    return redirect("/")