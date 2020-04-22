import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *
import sys
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/create")
def create():
    return render_template("create.html")
@app.route("/sign_up", methods=["POST"])
def registration():
    try:
        username = request.form.get("username")
        if username == "":
            return render_template("error.html", message= "Missing username!")
        password = request.form.get("password")
        if password == "":
            return render_template("error.html", message= "Missing password!")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        age = request.form.get("age")
        db.execute("INSERT INTO usuarios (username, password, first_name, last_name, age) VALUES (:username, :password, :first_name, :last_name, :age)", {"username":username, "password":password, "first_name":first_name, "last_name":last_name, "age":age})
        db.commit()
        return render_template("success2.html", message_1="Account created", message_2="You have succesfully created your account!")
    except:
        return render_template("error.html", message="Username already exists.")
@app.route("/login")
def login():
    return render_template("login.html")
@app.route("/login/check", methods=["POST"])
def check():
    username = request.form.get("username")
    if db.execute("SELECT * FROM usuarios WHERE username=:username", {"username": username}).rowcount == 0:
        return render_template("error.html", message="No such username, please try again or create one.")
    password = request.form.get("password")
    if db.execute("SELECT * FROM usuarios WHERE password=:password AND username=:username", {"password": password, "username": username}).rowcount == 0:
        return render_template("error.html", message="No such password, please try again")
    user = db.execute("SELECT * FROM usuarios WHERE password=:password AND username=:username", {"password": password, "username": username}).fetchone()
    session['loggedin'] = True
    session['id'] =  user.id
    session['username'] = user.username
    return render_template("index2.html", username=session['username'])
@app.route("/login/check/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))
@app.route("/login/check/books", methods=["POST"])
def books():
    try:
        search = request.form.get("book")
        if search == "":
            return render_template("error.html", message= "Missing any word!")
        books = db.execute("SELECT * FROM books WHERE title = :title OR author = :author OR isbn = :isbn ORDER BY title", {"title": search, "author": search, "isbn": search}).fetchall()
        return render_template("books.html", books=books)
    except:
        return render_template("error.html", message= "Don't have access to that book!")
@app.route("/login/check/books/<int:book_id>")
def book(book_id):
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "i9T2Tsr7K65kIjd9NH6lNg", "isbns":"{}".format(book.isbn)})
    data = res.json()
    rating = data['books'][0]['average_rating']
    number_of_ratings = data['books'][0]['work_ratings_count']
    title = book.title
    if book is None:
        return render_template("error.html", message="No such book")
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    return render_template("book.html", book=book, rating=rating, number_of_ratings=number_of_ratings, reviews=reviews, title=title)
@app.route("/login/check/books/<int:book_id>/submit", methods=["POST"])
def submit(book_id):
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    user_id = session['id']
    book_id = book.id
    title = request.form.get("title")
    if title == "":
        return render_template("error.html", message="Error, missing title.")
    score = int(float(request.form.get("score")))
    if score not in range(1,6):
        return render_template("error.html", message="Error, there is problem with the score. Please type a number in range 1-5.")
    review = request.form.get("review")
    if review == "":
        return render_template("error.html", message="Error, missing review text")
    rowcount = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id": user_id, "book_id": book_id}).rowcount
    if rowcount != 0:
        return render_template("error.html", message="You have already submitted a review of this book! You can only do this once.")
    db.execute("INSERT INTO reviews (title, review, score, book_id, user_id) VALUES (:title, :review, :score, :book_id, :user_id)", {"title":title, "review":review, "score":score, "book_id":book_id, "user_id":user_id})
    db.commit()
    return render_template("success.html", message_1="Submitted review", message_2="Thanks for your review! You help us growing everyday.")
@app.route("/api/<isbn>")
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "i9T2Tsr7K65kIjd9NH6lNg", "isbns":"{}".format(book.isbn)})
    data = res.json()
    title = book.title
    author = book.author
    year = book.year
    isbn = data['books'][0]['isbn']
    review_count = data['books'][0]['reviews_count']
    average_score = data['books'][0]['average_rating']
    if book is None:
        return jsonify({"error": "Invalid isbn"}), 422
    return jsonify({
            "title": title,
            "author": author,
            "year": year,
            "isbn": isbn,
            "review_count": review_count,
            "average_score": average_score
        })
