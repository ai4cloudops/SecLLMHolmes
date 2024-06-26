from flask import Blueprint, request, escape
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
    sanitized_title = escape(title) + ' by ' + author
    if result:
        return '<p>%s found</p>' % sanitized_title
    else:
        return '<p>%s not found</p>' % sanitized_title