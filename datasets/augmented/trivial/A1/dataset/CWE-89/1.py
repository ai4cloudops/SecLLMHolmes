import sqlite3

def delete_book(uj):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE title = '%s'" % uj)
    conn.commit()
    conn.close()
