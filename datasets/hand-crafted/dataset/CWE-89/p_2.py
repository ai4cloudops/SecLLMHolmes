from sqlalchemy import create_engine, MetaData, Table

engine = create_engine('sqlite:///books.db')
metadata = MetaData(bind=engine)

books = Table('books', metadata, autoload=True)

def insert_book(user_input):
    ins = books.insert().values(title=user_input)
    conn = engine.connect()
    conn.execute(ins)
    conn.close()

def find_book(user_input):
    result = engine.execute('select * from books where id = :id', id=user_input)
    if result:
        return result.first()