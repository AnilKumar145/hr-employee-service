from fastapi import FastAPI, HTTPException, Depends, status
from typing import List
from generate_employees import generate_employees
from models import Employee, StatusType
from auth import Token, User, authenticate_user, create_access_token, get_current_active_user
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Initialize FastAPI application with title
app = FastAPI(title="HR_Employee Service")

# In-memory database with 1000 fake employees
# This simulates a database for development/demo purposes
# In production, this would be replaced with a real database
employee_db: List[Employee] = [Employee(**data) for data in generate_employees(1000)]

# Default admin credentials for API access
# Username: admin
# Password: adminpassword

# Login endpoint - authenticates user and returns JWT token
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    from auth import fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES
    # Authenticate user credentials
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        # Return 401 if authentication fails
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create access token with expiration time
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # Return token for client to use in subsequent requests
    return {"access_token": access_token, "token_type": "bearer"}

# Protected routes - all require valid token
# Add new employee to the database
@app.post("/employees", response_model=Employee)
def add_employee(employee: Employee, current_user: User = Depends(get_current_active_user)):
    # Dependency injection ensures only authenticated users can access
    # Adds a new employee to the in-memory database
    employee_db.append(employee)
    return employee

# Get all employees from the database
@app.get("/employees", response_model=List[Employee])
def get_all_employees(current_user: User = Depends(get_current_active_user)):
    # Returns the complete list of employees
    # Requires authentication via JWT token
    return employee_db

# Get a specific employee by ID
@app.get("/employees/{employee_id}", response_model=Employee)
def get_employee_by_id(employee_id: str, current_user: User = Depends(get_current_active_user)):
    # Search for employee with matching ID
    # Returns 404 if employee not found
    for emp in employee_db:
        if emp.employee_id == employee_id:
            return emp
    # If no matching employee is found, raise 404 error
    raise HTTPException(status_code=404, detail="Employee not found")

# Update an employee's department
@app.put("/employees/{employee_id}/change-department")
def change_department(employee_id: str, new_department: str, current_user: User = Depends(get_current_active_user)):
    # Updates the department for a specific employee
    # Requires authentication and valid employee ID
    for emp in employee_db:
        if emp.employee_id == employee_id:
            emp.department = new_department
            return {"message": f"Department changed to {new_department} for employee {employee_id}"}
    # If employee not found, return 404 error
    raise HTTPException(status_code=404, detail="Employee not found")

# Mark an employee as resigned
@app.put("/employees/{employee_id}/resign")
def resign_employee(employee_id: str, current_user: User = Depends(get_current_active_user)):
    # Updates employee status to resigned and sets is_active to 0 (inactive)
    # Requires authentication and valid employee ID
    for emp in employee_db:
        if emp.employee_id == employee_id:
            emp.status = StatusType.resigned
            emp.is_active = 0
            return {"message": f"Employee {employee_id} marked as resigned"}
    # If employee not found, return 404 error
    raise HTTPException(status_code=404, detail="Employee not found")
