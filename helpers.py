import os
from functools import wraps
from flask import request, redirect, url_for, session


# Information taken from https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
# Information found in C$50 Finance helper functions

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# def error():
    # TO DO
    # Generate an error page with the correct code



def display_image(filename):
    print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)