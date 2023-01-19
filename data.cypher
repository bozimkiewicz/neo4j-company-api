CREATE (wpawlowski:Employee {name:"Wiesław", surname: "Pawłowski", position:"UI/UX"})
CREATE (jneumann:Employee {name:"Jakub", surname: "Neumann", position:"Fullstack"})
CREATE (mmiotk:Employee {name:"Mateusz", surname: "Miotk", position:"Tester"})
CREATE (wlojkowski:Employee {name:"Wojciech", surname: "Łojkowski", position:"Intern"})
CREATE (atejszerska:Employee {name:"Aleksandra", surname: "Tejszerska", position:"Recruiter"})

CREATE (HR:Department {name:"HR"})
CREATE (IT:Department {name:"IT"})

MATCH (a:Employee), (b:Department) WHERE a.name = 'Jakub' AND b.name = 'IT' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)
MATCH (a:Employee), (b:Department) WHERE a.name = 'Wiesław' AND b.name = 'IT' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)
MATCH (a:Employee), (b:Department) WHERE a.name = 'Mateusz' AND b.name = 'IT' CREATE (a)-[r:WORKS_IN]->(b)<-[:MANAGES]-(a) RETURN type(r)
MATCH (a:Employee), (b:Department) WHERE a.name = 'Wojciech' AND b.name = 'HR' CREATE (a)-[r:WORKS_IN]->(b)<-[:MANAGES]-(a) RETURN type(r)
MATCH (a:Employee), (b:Department) WHERE a.name = 'Aleksandra' AND b.name = 'HR' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)