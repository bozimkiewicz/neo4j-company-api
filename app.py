from helper_functions import *
from dotenv import load_dotenv
from neo4j import GraphDatabase
from flask import Flask, jsonify, request
import os
import re

load_dotenv()
app = Flask(__name__)
uri = os.getenv('URI')
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")



@app.route('/employees', methods=['GET'])
def get_employees_route():
    args = request.args
    sort = args.get("sort")
    sortType = args.get("sortType")
    filter = args.get("filter")
    filterType = args.get("filterType")
    with driver.session() as session:
        employees = session.execute_read(get_employees, sort, sortType, filter, filterType)
    response = {'employees': employees}
    return jsonify(response)



@app.route('/employees', methods=['POST'])
def add_employee_route():
    name = request.form['name']
    surname = request.form['surname']
    position = request.form['position']
    department = request.form['department']
    if(name == '' or surname == '' or position == '' or department == ''):
        return 'Not a complete request'

    with driver.session() as session:
        session.execute_write(add_employee, name, surname, position, department)

    response = {'status': 'success'}
    return jsonify(response)



@app.route('/employees/<string:person>', methods=['PUT'])
def update_employee_route(person):
    person_1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person_1[0]
    surname = person_1[1]
    updated_name = request.form['name']
    updated_surname = request.form['surname']
    updated_department = request.form['department']
    updated_position = request.form['position']

    with driver.session() as session:
        employee = session.write_transaction(
            update_employee, name, surname, updated_name, updated_surname, updated_department, updated_position)

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)



@app.route('/employees/<string:person>', methods=['DELETE'])
def delete_employee_route(person):
    person_1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person_1[0]
    surname = person_1[1]
    with driver.session() as session:
        employee = session.write_transaction(delete_employee, name, surname)

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)



@app.route('/employees/<person>/subordinates', methods=['GET'])
def get_employees_subordinates_route(person):
    person_1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person_1[0]
    surname = person_1[1]
    with driver.session() as session:
        employees = session.read_transaction(get_employees_subordinates, name, surname)
    response = {'employees': employees}
    return jsonify(response)



@app.route('/departments', methods=['GET'])
def get_departments_route():
    with driver.session() as session:
        departments = session.read_transaction(get_departments)
    response = {'departments': departments}
    return jsonify(response)



@app.route('/employees/<string:person>/department', methods=['GET'])
def get_departments_route_from_employee(person):
    person_1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person_1[0]
    surname = person_1[1]
    with driver.session() as session:
        departments = session.read_transaction(get_departments_from_employee, name, surname)
    response = {'department': departments}
    return jsonify(response)



@app.route('/departments/<string:name>/employees', methods=['GET'])
def get_departments_route_from_department(name):
    with driver.session() as session:
        employees = session.execute_read(get_departments_employees, name)
    response = {'employees': employees}
    return jsonify(response)



if __name__ == '__main__':
    app.run()