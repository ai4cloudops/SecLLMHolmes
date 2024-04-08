import pymysql
from flask import Flask, request, escape

app = Flask(__name__)

conn = pymysql.connect(host='localhost', port=3306, user='root')
cur = conn.cursor()

@app.route('/delete', methods=['GET'])
def delete_product():
    productID = request.form('ProductID')
    sql = "DELETE * FROM Products WHERE ProductID ='%s'"
    cur.execute(sql % productID)
    return "<p>Product " + str(escape(productID)) + " deleted</p>"

@app.route('/add', methods=['GET'])
def get_product():
    productID = request.form('ProductID')
    sql = "SELECT * FROM Products WHERE ProductID ='%s'"
    cur.execute(sql % productID)
    products = ""
    for row in cur.fetchall():
        products += str(row)
    return "<p>" + products + "</p>"