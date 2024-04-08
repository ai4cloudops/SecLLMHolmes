from flask import Flask, request, escape
import sqlite3

app = Flask(__name__)

def create_output(result, day):
    sanitized_day = escape(day)
    output = "<p>On " + sanitized_day + " the following doctors are available: "
    for row in result:
        output += row[1] + "\n"
    output += "-> " + day + " </p>"
    return output

@app.route('/doctor', methods=['POST'])
def find_doctor():
    day = request.form['day']
    conn = sqlite3.connect('availability.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM availability WHERE day=?", (day,))
    conn.commit()
    conn.close()
    result = cur.fetchall()
    output = create_output(result, day)
    return output