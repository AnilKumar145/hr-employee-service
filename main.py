from fastapi import FastAPI, HTTPException
from typing import List
from models import Employee
from generate_employees import generate_employees

app = FastAPI(title="HR_Employee Service")

# In-memory database with 100 fake employees

employee_db: List[Employee] = [Employee(**data) for data in generate_employees(1000)]

@app.post("/employees", response_model=Employee)
def add_employee(employee: Employee):
    employee_db.append(employee)
    return employee

@app.get("/employees", response_model=List[Employee])
def get_all_employees():
    return employee_db

@app.get("/employees/{employee_id}", response_model=Employee)
def get_employee_by_id(employee_id: str):
    for emp in employee_db:
        if emp.employee_id == employee_id:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found")
@app.get("/employees/count")
def count_employees():
    return {"total_employees": len(employee_db)}
