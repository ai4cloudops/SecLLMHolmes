from flask import Flask, request, escape
from sqlalchemy import create_engine, MetaData, Table

engine = create_engine('sqlite:///users.db')
metadata = MetaData(bind=engine)
users = Table('users', metadata, autoload=True)

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    result = engine.execute('select * from users where username = :username and password = :password', username=username, password=password).first()
    if result:
        return '<p>Hello ' + str(escape(username)) + '</p>'
    else:
        return '<p>Wrong username or password</p>'