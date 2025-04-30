from fastapi import FastAPI, HTTPException, Depends, status
from typing import List
from generate_employees import generate_employees
from models import Employee, StatusType
from auth import Token, User, UserCreate, authenticate_user, create_access_token, get_current_active_user, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

app = FastAPI(title="HR_Employee Service")

# In-memory database with 1000 fake employees
employee_db: List[Employee] = [Employee(**data) for data in generate_employees(1000)]

# Public endpoints (no authentication required)
@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    from auth import fake_users_db
    if user_data.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user with hashed password
    fake_users_db[user_data.username] = {
        "username": user_data.username,
        "full_name": user_data.full_name,
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "disabled": False,
    }
    
    # Return user without password
    return {
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "disabled": False
    }

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    from auth import fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected routes - all require valid token
@app.post("/employees", response_model=Employee)
def add_employee(employee: Employee, current_user: User = Depends(get_current_active_user)):
    employee_db.append(employee)
    return employee

@app.get("/employees", response_model=List[Employee])
def get_all_employees(current_user: User = Depends(get_current_active_user)):
    return employee_db

@app.get("/employees/{employee_id}", response_model=Employee)
def get_employee_by_id(employee_id: str, current_user: User = Depends(get_current_active_user)):
    for emp in employee_db:
        if emp.employee_id == employee_id:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found")

@app.put("/employees/{employee_id}/change-department")
def change_department(employee_id: str, new_department: str, current_user: User = Depends(get_current_active_user)):
    for emp in employee_db:
        if emp.employee_id == employee_id:
            emp.department = new_department
            return {"message": f"Department changed to {new_department} for employee {employee_id}"}
    raise HTTPException(status_code=404, detail="Employee not found")

@app.put("/employees/{employee_id}/resign")
def resign_employee(employee_id: str, current_user: User = Depends(get_current_active_user)):
    for emp in employee_db:
        if emp.employee_id == employee_id:
            emp.status = StatusType.resigned
            emp.is_active = False
            return {"message": f"Employee {employee_id} marked as resigned"}
    raise HTTPException(status_code=404, detail="Employee not found")
