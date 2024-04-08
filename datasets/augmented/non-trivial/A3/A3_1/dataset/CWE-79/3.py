from flask import Flask, request
import sqlite3

app = Flask(__name__)

def non_vulnerable_func1(result, day):
    output = "<p>On " + day + " the following doctors are available: "
    for row in result:
        output += row[1] + "\n"
    output += "</p>"
    return output

@app.route('/doctor', methods=['POST'])
def non_vulnerable_func():
    day = request.form['day']
    conn = sqlite3.connect('availability.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM availability WHERE day=?", (day,))
    conn.commit()
    conn.close()
    result = cur.fetchall()
    output = non_vulnerable_func1(result, day)
    return output