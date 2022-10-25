from bson import ObjectId
from flask import *
from flask_bootstrap import Bootstrap
from flask_pymongo import PyMongo
from flask_moment import Moment
from datetime import datetime
import json

fl = Flask("ranker")
Bootstrap(fl)
moment = Moment(fl)
fl.config["SECRET_KEY"] = "RANDOMkey"
fl.config['MONGO_URI'] = "mongodb://localhost:27017/ranker-db"
mongo = PyMongo(fl)

@fl.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

@fl.route("/",methods=["GET","POST"])
def register():
    if "info" in session:
        flash("You are already logged in.")
        return redirect("/user")
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        exist = mongo.db.loginInfo.find_one({"email": request.form['email']})
        if exist is None:
            doc={}
            for item in request.form:
                doc[item] = request.form[item]
            mongo.db.loginInfo.insert_one(doc)
            print("new acc created")
            flash("Account created successfully!")
            return redirect("/login")
        else:
            flash("This email has already been used!")
            return redirect("/")

@fl.route("/login",methods=["GET","POST"])
def login():
    if "info" in session:
        flash("You are already logged in.")
        return redirect("/user")
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        doc = {"email": request.form["email"], "password": request.form["password"]}
        exist = mongo.db.loginInfo.find_one(doc)
        if exist is None:
            flash('The information you entered does not match our records. Please try again.')
            return redirect("/login")
        else:
            session["info"] = {'firstName': exist['firstName'], 'lastName': exist['lastName'], 'email': exist['email'], 'time': datetime.utcnow()}
            return redirect("/user")

@fl.route("/user", methods=["GET","POST"])
def user():
    if "info" not in session:
        flash("Error: You must log in before accessing this page.")
        return redirect("/login")
    if request.method == "GET":
        return render_template("home.html")
    elif request.method == "POST":
        entry = {"post": request.form["entry"], "user": session["info"]["email"], "time": datetime.utcnow()}
        mongo.db.loginInfo.insert(entry)
        flash("Your entry has been saved successfully.")
        return redirect("/user")

@fl.route("/add", methods=["GET","POST"])
def add():
    if request.method == "GET":
        return render_template("newranker.html")
    elif request.method == "POST":
        document = {}
        for item in request.form:
            global doc
            document[item]=request.form[item]
            doc = document[item]
            entry = {"post": doc, "user": session["info"]["email"], "time": datetime.utcnow()}
        mongo.db.itemlists.insert_one(entry)
        flash("Your list was saved successfully!")
        return redirect("/rankmaker")

@fl.route("/view", methods=["GET","POST","SEARCH"])
def view():
    allData = mongo.db.rankings.find({'user': session['info']['email']}).sort('time', -1)
    if request.method == "GET":
        return render_template("viewrankings.html", allRankings = allData)
    elif request.method == "POST":
        global searchData
        for item in request.form:
            if request.form['search'] != "":
                search = request.form['search']
                searchData = searching(search)
                return redirect("/viewSearch")
            else:
                return redirect("/user")

def searching(search):
    allData = mongo.db.rankings.find({'user': session['info']['email']}).sort('time', -1)
    newdata = []
    for data in allData:
        data['title'] = data['title'].lower()
        newdata.append(data)
    searchResults = []
    for data in newdata:
        if data['title'] == search.lower():
            searchResults.append(data)
    return searchResults

@fl.route("/viewSearch", methods=["GET","POST"])
def viewSearch():
    if request.method == "GET":
        return render_template("viewsearch.html", allSearches=searchData)
    if request.method == "POST":
        return redirect("/view")

@fl.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")
    elif request.method == "POST":
        flash("Ranking successfully uploaded!")
        for item in request.form:
            title = request.form['title']
            filename = request.form['filename']
        entry = {"title": title, "filename": filename, "user": session["info"]["email"], "time": datetime.utcnow()}
        mongo.db.rankings.insert_one(entry)
        return redirect("/user")

@fl.route("/rankmaker", methods=["GET", "POST"])
def makeRank():
    if request.method == "GET":
        itemlist = doc.split(",")
        return render_template("rankmaker.html",items = json.dumps(itemlist))
    if request.method == "POST":
        return redirect("/user")

@fl.route("/delete/<id>")
def delRoute(id):
    #ids are not strings they are ObjectId('')
    #html has all strings
    flash("Ranking has been deleted")
    delItem = mongo.db.rankings.find_one({'_id': ObjectId(id)})
    mongo.db.rankings.delete_one(delItem)
    return redirect("/user")

@fl.route("/logout")
def out():
    session.clear()
    flash("You have been logged out.")
    return redirect("/login")

@fl.errorhandler(404)
def noPage(error):
    #error starting with 2 ex: 200 is ok, 302 is redirect, 404 is not found (status codes)
    return render_template("error.html",error=error)

fl.run(debug=True)
