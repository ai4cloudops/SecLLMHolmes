from sqlalchemy import create_engine, MetaData, Table

engine = create_engine('sqlite:///books.db')
metadata = MetaData(bind=engine)

books = Table('books', metadata, autoload=True)

def insert_book(ie):
    ins = books.insert().values(title=ie)
    conn = engine.connect()
    conn.execute(ins)
    conn.close()

def find_book(ba):
    result = engine.execute('select * from books where id = ' + ba)
    if result:
        return result.first()