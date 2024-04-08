import pymysql
from flask import Flask, request

app = Flask(__name__)

session = {}

def createQuery(pv, xs):
  query_text = "SELECT * FROM users WHERE pv = '%s' AND xs = '%s'"
  parmeters = (pv, xs)
  query = query_text, parmeters
  return query

@app.route("/login")
def login():
  pv = request.form('pv')
  xs = request.form('xs')

  db = pymysql.connect("localhost")
  cursor = db.cursor()

  query = createQuery(pv, xs)
  cursor.execute(query)

  record = cursor.fetchone()
  if record:
    session['logged_user'] = pv
    return "<p>Logged in!</p>"
  db.close()