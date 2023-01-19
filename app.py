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

def get_employees(neo, sortType='', sort='', filterType='', filter=''):
    query = "MATCH (m:Employee) RETURN m"
    match sortType:
        case 'asc':
            match sort:
                case 'name':
                    query = "MATCH (m:Employee) RETURN m ORDER BY m.name"
                case 'surname':
                    query = "MATCH (m:Employee) RETURN m ORDER BY m.surname"
                case 'position':
                    query = "MATCH (m:Employee) RETURN m ORDER BY m.position"
        case 'desc':        
            match sort:
                case 'name':
                    query = "MATCH (m:Employee) RETURN m ORDER BY m.name DESC"
                case 'surname':
                    query = "MATCH (m:Employee) RETURN m ORDER BY m.surname DESC"
                case 'position':
                    query = "MATCH (m:Employee) RETURN m ORDER BY m.position DESC"    
    match filterType:
        case 'name':
            query = f"MATCH (m:Employee) WHERE m.name CONTAINS '{filter}' RETURN m"          
        case 'surname':
            query = f"MATCH (m:Employee) WHERE m.surname CONTAINS '{filter}' RETURN m"   
        case 'position':
            query = f"MATCH (m:Employee) WHERE m.position CONTAINS '{filter}' RETURN m"                 
    results = neo.run(query).data()
    employees = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return employees


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


def update_employee(neo, name, surname, updated_name, updated_surname, updated_department, updated_position):
    query = f"MATCH (m:Employee)-[r]-(d:Department) WHERE m.name='{name}' AND m.surname='{surname}' RETURN m,d,r"
    result = neo.run(query, name=name, surname=surname).data()
    print(result)
    print(result[1]['r'][1])
    if not result:
        return None
    else:
        query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' SET m.name='{updated_name}', m.surname='{updated_surname}', m.position='${updated_position}'"
        query_1 = f"MATCH (m:Employee {{name: '{name}', surname: '{surname}'}})-[r:WORKS_IN]->(d:Department {{name:'{result[0]['d']['name']}'}}) DELETE r"
        query_2 = f"""MATCH (a:Employee),(b:Department) WHERE a.name = '{name}' AND a.surname = '{surname}' AND b.name = '{updated_department}' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)"""
        neo.run(query, name=name, surname=surname, updated_name=updated_name, updated_surname=updated_surname, updated_position=updated_position)
        neo.run(query_1, name=name, surname=surname)
        neo.run(query_2, name=name, surname=surname, updated_department=updated_department)
        return {'name': updated_name, 'surname': updated_surname, 'position':updated_position, 'updated department': updated_department}


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
            update_employee,name, surname, updated_name, updated_surname, updated_department, updated_position)

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)


def delete_employee(neo, name, surname):
    query = f"MATCH (m:Employee)-[r]-(d:Department) WHERE m.name='{name}' AND m.surname='{surname}' RETURN m,d,r"
    result = neo.run(query, name=name, surname=surname).data()
    if not result:
        return None
    else:
        query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' DETACH DELETE m"
        neo.run(query, name=name, surname=surname)
        if(len(result) > 1):
            query = f"MATCH (m:Employee)-[r:WORKS_IN]-(d:Department {{name:'{result[0]['d']['name']}'}}) RETURN m"
            results = neo.run(query).data()
            if(len(results) == 0):
                query = f"MATCH (d:Department) WHERE d.name='{result[0]['d']['name']}' DETACH DELETE d"
                neo.run(query, name=name, surname=surname)
            employees = [{'name': result['m']['name'], 'surname': result['m']['surname'], 'position': result['m']['position']} for result in results]
            query_2 = f"""MATCH (a:Employee),(b:Department) WHERE a.name = '{employees[0]['name']}' AND a.surname = '{employees[0]['surname']}' AND b.name = '{result[0]['d']['name']}' CREATE (a)-[r:MANAGES]->(b) RETURN type(r)"""
            neo.run(query_2)
        return {'name': name, 'surname':surname}


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


def get_employees_subordinates(neo, name, surname):
    query = f"""MATCH (p:Employee), (p1:Employee {{name:'{name}', surname:'{surname}'}})-[r]-(d) 
               WHERE NOT (p)-[:MANAGES]-(:Department) 
               AND (p)-[:WORKS_IN]-(:Department {{name:d.name}}) 
               RETURN p"""
    results = neo.run(query).data()
    employees = [{'name': result['p']['name'],
               'surname': result['p']['surname']} for result in results[:len(results)//2]]
    return employees


@app.route('/employees/<person>/subordinates', methods=['GET'])
def get_employees_subordinates_route(person):
    person_1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person_1[0]
    surname = person_1[1]
    with driver.session() as session:
        employees = session.read_transaction(get_employees_subordinates, name, surname)
    response = {'employees': employees}
    return jsonify(response)


def get_departments(neo, sortType='', sort='', filterType='', filter=''):
    query = "MATCH (m:Department) RETURN m"
    match sortType:
        case 'asc':
            match sort:
                case 'name':
                    query = "MATCH (m:Department) RETURN m ORDER BY m.name"
                case 'numberOfEmployees':
                    query = f"""MATCH 
                        (m:Employee)-[r:WORKS_IN]-(d:Department)
                        RETURN d.name ORDER BY count(m)"""    
        case 'desc':        
            match sort:
                case 'name':
                    query = "MATCH (m:Department) RETURN m ORDER BY m.name DESC"
                case 'numberOfEmployees':
                    query = f"""MATCH 
                        (m:Employee)-[r:WORKS_IN]-(d:Department)
                        RETURN d.name ORDER BY count(m) DESC"""    
    match filterType:
        case 'name':
            query = f"MATCH (m:Department) WHERE m.name CONTAINS '{filter}' RETURN m"          
        case 'numberOfEmployees':
            query = f"""MATCH 
               (m:Employee)-[r:WORKS_IN]-(d:Department)
               WHERE count(m) = '{filter}'               
               RETURN d.name"""     
    results = neo.run(query).data()
    departments = [{'name': result['m']['name']} for result in results]
    return departments


@app.route('/departments', methods=['GET'])
def get_departments_route():
    with driver.session() as session:
        departments = session.read_transaction(get_departments)
    response = {'departments': departments}
    return jsonify(response)


def get_departments_from_employee(neo, name, surname):
    query = f"""MATCH 
               (m:Employee {{name:'{name}', surname:'{surname}'}})-[r:WORKS_IN]-(d:Department), 
               (m1:Employee)-[r1:MANAGES]-(d1:Department {{name:d.name}}),
               (m2:Employee)-[r2:WORKS_IN]-(d2:Department {{name:d.name}}) 
               RETURN d.name AS name, m1.name AS Manager, count(m2) AS Number_of_Employees"""
    result = neo.run(query).data()
    departments = [{'Name': result[0]['name'], 'Manager': result[0]['Manager'], 'Number of employees':result[0]['Number_of_Employees']+1 }]
    return departments


@app.route('/employees/<string:person>/department', methods=['GET'])
def get_departments_route_from_employee(person):
    person_1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person_1[0]
    surname = person_1[1]
    with driver.session() as session:
        departments = session.read_transaction(get_departments_from_employee, name, surname)
    response = {'department': departments}
    return jsonify(response)


def get_departments_employees(neo, name):
    query = f"MATCH (m:Employee)-[r:WORKS_IN]-(d:Department {{name:'{name}'}}) RETURN m"
    results = neo.run(query).data()
    employees = [{'name': result['m']['name'], 'surname': result['m']['surname'], 'position': result['m']['position']} for result in results]
    return employees


@app.route('/departments/<string:name>/employees', methods=['GET'])
def get_departments_route_from_department(name):
    with driver.session() as session:
        employees = session.execute_read(get_departments_employees, name)
    response = {'employees': employees}
    return jsonify(response)


def add_employee(neo, name, surname, position, department):
    query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' AND m.position='{position}' RETURN m"
    result = neo.run(query, name=name).data()
    if not result: 
        query = f"CREATE ({name}:Employee {{name:'{name}', surname:'{surname}', position:'{position}'}})"
        query_2 = f"MATCH (a:Employee),(b:Department) WHERE a.name = '{name}' AND a.surname = '{surname}' AND b.name = '{department}' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)"
        neo.run(query, name=name, surname=surname, position=position)
        neo.run(query_2, name=name, surname=surname, department=department)
    else:
        return 'Person exist'


if __name__ == '__main__':
    app.run()