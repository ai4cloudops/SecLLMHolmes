import pymysql
from flask import Flask, request

app = Flask(__name__)

session = {}

def createQuery(zb, mc):
  query_text = "SELECT * FROM users WHERE zb = '%s' AND mc = '%s'"
  parmeters = (zb, mc)
  query = query_text % parmeters
  return query

@app.route("/login")
def login():
  zb = request.form('zb')
  mc = request.form('mc')

  db = pymysql.connect("localhost")
  cursor = db.cursor()

  query = createQuery(zb, mc)
  cursor.execute(query)

  record = cursor.fetchone()
  if record:
    session['logged_user'] = zb
    return "<p>Logged in!</p>"
  db.close()