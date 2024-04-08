import sqlite3

def vulnerable_func(user_input):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE title = ?", (user_input,))
    conn.commit()
    conn.close()
