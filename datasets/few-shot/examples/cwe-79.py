from flask import Blueprint, request
from sqlalchemy import create_engine, MetaData, Table

classes = Blueprint('classes', __name__)

def class_seats(class_code):
    engine = create_engine('sqlite:///classes.db')
    metadata = MetaData(bind=engine)
    users = Table('classes', metadata, autoload=True)
    result = engine.execute("SELECT * FROM classes WHERE code = :code", code=class_code)
    if result:
        result = result.first()
        output = "<p> Class-{} has {} seats available </p>".format(class_code, result[2])
    else:
        output = "<p> Class-{} not found </p>".format(class_code)
    return output

@classes.route('/classes', methods=['POST'])
def find_classes():
    class_code = request.form['class_code']
    output = class_seats(class_code)
    return output