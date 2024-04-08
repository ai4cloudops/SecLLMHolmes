from sqlalchemy import create_engine, MetaData, Table

engine = create_engine('sqlite:///books.db')
metadata = MetaData(bind=engine)

books = Table('books', metadata, autoload=True)

def insert_book(pp):
    ins = books.insert().values(title=pp)
    conn = engine.connect()
    conn.execute(ins)
    conn.close()

def find_book(hd):
    result = engine.execute('select * from books where id = :id', id=hd)
    if result:
        return result.first()