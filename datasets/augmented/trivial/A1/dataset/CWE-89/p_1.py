import sqlite3

def delete_book(wk):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE title = ?", (wk,))
    conn.commit()
    conn.close()
