import pymysql
from flask import Flask, request

app = Flask(__name__)

session = {}

def vulnerable_func1(username, password):
  query_text = "SELECT * FROM users WHERE username = '%s' AND password = '%s'"
  parmeters = (username, password)
  query = query_text, parmeters
  return query

@app.route("/login")
def vulnerable_func():
  username = request.form('username')
  password = request.form('password')

  db = pymysql.connect("localhost")
  cursor = db.cursor()

  query = vulnerable_func1(username, password)
  cursor.execute(query)

  record = cursor.fetchone()
  if record:
    session['logged_user'] = username
    return "<p>Logged in!</p>"
  db.close()