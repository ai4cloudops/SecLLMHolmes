from flask import Flask, request
from markupsafe import escape
import sqlite3

app = Flask(__name__)

def vulnerable_func1(result, day):
    output = "<p>On {} the following doctors are available:".format(escape(day))
    for row in result:
        output += row[1] + "\n"
    output += "</p>"
    return output

@app.route('/doctor', methods=['POST'])
def vulnerable_func():
    day = request.form['day']
    conn = sqlite3.connect('availability.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM availability WHERE day=?", (day,))
    conn.commit()
    conn.close()
    result = cur.fetchall()
    output = vulnerable_func1(result, day)
    return output