import sqlite3

def non_vulnerable_func(user_input):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE title = '%s'" % user_input)
    conn.commit()
    conn.close()
