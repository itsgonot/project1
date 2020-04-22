from flask_sqlalchemy import SQLAlchemy

db= SQLAlchemy()

class User(db.Model):
    __tablename__="usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    age = db.Column(db.Integer)
