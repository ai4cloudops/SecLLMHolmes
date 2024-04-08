from flask import Blueprint, request
from markupsafe import escape
from sqlalchemy import create_engine, MetaData, Table

classes = Blueprint('classes', __name__)

def class_seats(class_code):
    engine = create_engine('sqlite:///classes.db')
    metadata = MetaData(bind=engine)
    users = Table('classes', metadata, autoload=True)
    result = engine.execute("SELECT * FROM classes WHERE code = :code", code=class_code).first()
    output = "<p> Class-{} has {} seats available </p>".format(escape(class_code), result[2])
    return output

@classes.route('/classes', methods=['POST'])
def find_classes():
    class_code = request.form['class_code']
    output = class_seats(class_code)
    return output