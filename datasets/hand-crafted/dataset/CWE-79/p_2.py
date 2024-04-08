from flask import Blueprint, request
from markupsafe import escape
import sqlite3

book = Blueprint('book', __name__)

@book.route('/find', methods=['POST'])
def find():
    title = request.form['title']
    author = request.form['author']
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM books WHERE title = ? and author = ?', (title, author))
    result = cursor.fetchone()
    if result:
        return '<p>%s found</p>' % escape(title)
    else:
        return '<p>%s not found</p>' % escape(title)