
from typing import List, Optional, Dict, Any
import json
import os
from fastapi import FastAPI, Depends, HTTPException, status, Security, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
# Import only the models that exist in your models.py file
from models import Employee, StatusType, EmploymentType
from auth import (
    Token, User, authenticate_user, create_access_token, 
    fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user_from_token, get_current_user_from_bearer,
    get_current_user_basic
)
from generate_employees import generate_employees

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    auto_error=False  # Don't auto-raise errors for missing tokens
)

# Define enhanced response models
class EmployeeCreateResponse(BaseModel):
    message: str
    employee_id: str
    details: Employee
    timestamp: str

class EmployeeDepartmentChangeResponse(BaseModel):
    message: str
    changes: Dict[str, str]
    employee_id: str
    details: Employee
    timestamp: str

class EmployeeResignResponse(BaseModel):
    message: str
    employee_id: str
    employment_duration: str
    last_department: str
    last_role: str
    resignation_date: str
    details: Employee
    timestamp: str

# Initialize FastAPI app with Swagger UI configuration and documentation
app = FastAPI(
    title="HR Employee Service",
    description="""
    API for HR employee management
    
    ## Authentication
    
    Use the following credentials to access the API:
    - Username: admin
    - Password: adminpassword
    
    First use the /login endpoint or the Authorize button to get a token.
    """,
    swagger_ui_parameters={"persistAuthorization": True}  # Keep authorization between refreshes
)

# IMPORTANT: Add SessionMiddleware FIRST
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# Then add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory employee storage
employees_db = []

# Load sample employees or generate new ones
def load_employees():
    try:
        # Try to load from sample_employees.json
        with open("sample_employees.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Generate new employees if file doesn't exist or is invalid
        return generate_employees(100)

# Initialize employees data
employees_db = load_employees()

# Function to convert existing employee data to new format
def convert_employee_data():
    for employee in employees_db:
        if "name" in employee and "first_name" not in employee:
            # Split name into first_name and last_name
            name_parts = employee["name"].split(" ", 1)
            employee["first_name"] = name_parts[0]
            employee["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
            del employee["name"]
            
        # Convert address to separate fields
        if "address" in employee:
            address_parts = employee["address"].split(", ", 3)
            employee["street"] = address_parts[0] if len(address_parts) > 0 else ""
            employee["city"] = address_parts[1] if len(address_parts) > 1 else ""
            state_zip = address_parts[2].split(" ", 1) if len(address_parts) > 2 else ["", ""]
            employee["state"] = state_zip[0]
            employee["country"] = "USA"  # Default country
            del employee["address"]
            
        # Convert is_active to 0/1
        if "is_active" in employee and isinstance(employee["is_active"], bool):
            employee["is_active"] = 1 if employee["is_active"] else 0

# Convert existing data when app starts
convert_employee_data()

# Employee data access functions
def get_employees(skip: int = 0, limit: int = 100):
    return employees_db[skip: skip + limit]

def get_employee_by_id(employee_id: str):
    for employee in employees_db:
        if employee["employee_id"] == employee_id:
            return employee
    return None

def create_employee(employee: dict):
    # Generate a new employee ID
    max_id = 1000
    for emp in employees_db:
        emp_id = int(emp["employee_id"].replace("EMP", ""))
        if emp_id > max_id:
            max_id = emp_id
    
    new_employee = employee.copy()
    new_employee["employee_id"] = f"EMP{max_id + 1}"
    
    employees_db.append(new_employee)
    return new_employee

def update_employee(employee_id: str, employee_update: dict):
    for i, employee in enumerate(employees_db):
        if employee["employee_id"] == employee_id:
            # Update only the fields that are provided
            updated_employee = {**employee, **employee_update}
            employees_db[i] = updated_employee
            return updated_employee
    return None

def delete_employee(employee_id: str):
    for i, employee in enumerate(employees_db):
        if employee["employee_id"] == employee_id:
            employees_db.pop(i)
            return True
    return False

# Global token storage (for development/testing only)
CURRENT_TOKEN = None

# Login endpoint - authenticates user and returns JWT token
@app.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    global CURRENT_TOKEN
    
    # Authenticate user credentials
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        # Return 401 if authentication fails
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create access token with expiration time
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Store token globally (for development/testing only)
    CURRENT_TOKEN = access_token
    
    # Store token in session
    request.session["access_token"] = access_token
    
    # Set token in cookie
    response.set_cookie(
        key="access_token", 
        value=access_token,
        httponly=False,
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Create a middleware to safely handle token
@app.middleware("http")
async def add_token_to_header(request: Request, call_next):
    # Skip for login endpoint
    if request.url.path == "/login":
        return await call_next(request)
    
    # Try to get token from cookie first (more reliable)
    token = request.cookies.get("access_token")
    
    # Then try session if available
    if not token and "session" in request.scope:
        try:
            token = request.session.get("access_token")
        except Exception:
            # Handle any session-related errors gracefully
            pass
    
    # If token exists, add it to request headers
    if token:
        # Add token to headers safely - replace any existing Authorization header
        try:
            # Remove any existing Authorization header
            request.headers.__dict__["_list"] = [
                (k, v) for k, v in request.headers.__dict__["_list"] 
                if k.decode().lower() != "authorization"
            ]
            # Add the token from session/cookie
            request.headers.__dict__["_list"].append(
                (b"authorization", f"Bearer {token}".encode())
            )
        except Exception:
            # If we can't modify headers, continue anyway
            pass
    
    # Process the request
    response = await call_next(request)
    return response

# Get current user from token with global fallback
async def get_current_user_with_global_fallback(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    global CURRENT_TOKEN
    
    if not token:
        # Try cookie
        token = request.cookies.get("access_token")
        
        # Try session
        if not token and "session" in request.scope:
            try:
                token = request.session.get("access_token")
            except Exception:
                pass
        
        # Fall back to global token
        if not token:
            token = CURRENT_TOKEN
    
    # Rest of your token validation logic...
    # ... (you would typically validate the token here)

# Protected endpoint that accepts JWT token authentication
@app.get("/employees/", response_model=List[Employee])
async def read_employees(
    current_user: User = Depends(get_current_user_from_token),
    skip: int = 0, 
    limit: int = 100
):
    """
    Get all employees with pagination.
    This endpoint uses JWT token authentication.
    """
    employees = get_employees(skip=skip, limit=limit)
    return [Employee.model_validate(emp) for emp in employees]

# Get a specific employee by ID
@app.get("/employees/{employee_id}", response_model=Employee)
async def read_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a specific employee by ID"""
    employee = get_employee_by_id(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return Employee.model_validate(employee)

# Create a new employee
@app.post("/employees/", response_model=EmployeeCreateResponse)
async def create_new_employee(
    employee: Employee,
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new employee"""
    # Convert Pydantic model to dict
    employee_dict = employee.model_dump()
    
    # Ensure is_active is 0 or 1, not boolean
    if isinstance(employee_dict["is_active"], bool):
        employee_dict["is_active"] = 1 if employee_dict["is_active"] else 0
        
    # Create the employee
    new_employee = create_employee(employee_dict)
    
    # Return enhanced response
    return EmployeeCreateResponse(
        message=f"✅ Employee {new_employee['first_name']} {new_employee['last_name']} created successfully!",
        employee_id=new_employee["employee_id"],
        details=Employee.model_validate(new_employee),
        timestamp=datetime.now().isoformat()
    )


# Update an existing employee's department
@app.put("/employees/{employee_id}/change-department", response_model=EmployeeDepartmentChangeResponse)
async def update_employee_department(
    employee_id: str,
    department: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user_from_token)
):
    """Update an employee's department"""
    # Find the employee
    employee = get_employee_by_id(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Store old department for response
    old_department = employee["department"]
    
    # Update only the department field
    employee_update = {"department": department}
    
    # Update the employee
    updated_employee = update_employee(employee_id, employee_update)
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Return enhanced response
    return EmployeeDepartmentChangeResponse(
        message=f"🔄 Department changed successfully for {updated_employee['first_name']} {updated_employee['last_name']}!",
        changes={
            "from": old_department,
            "to": department
        },
        employee_id=employee_id,
        details=Employee.model_validate(updated_employee),
        timestamp=datetime.now().isoformat()
    )

# Resign an employee using PUT method
@app.put("/employees/{employee_id}/resign", response_model=EmployeeResignResponse)
async def resign_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Resign an employee (change status to Resigned and is_active to 0)"""
    # Find the employee
    employee = get_employee_by_id(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate employment duration
    start_date = datetime.strptime(employee["start_date"], "%Y-%m-%d")
    end_date = datetime.now(timezone.utc)
    duration_days = (end_date.date() - start_date.date()).days
    years = duration_days // 365
    months = (duration_days % 365) // 30
    days = (duration_days % 365) % 30
    
    # Update status to Resigned and is_active to 0
    employee_update = {
        "status": "Resigned",
        "is_active": 0,
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    # Update the employee
    updated_employee = update_employee(employee_id, employee_update)
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Return enhanced response
    return EmployeeResignResponse(
        message=f"👋 {updated_employee['first_name']} {updated_employee['last_name']} has resigned!",
        employee_id=employee_id,
        employment_duration=f"{years} years, {months} months, {days} days",
        last_department=updated_employee["department"],
        last_role=updated_employee["role"],
        resignation_date=end_date.strftime("%Y-%m-%d"),
        details=Employee.model_validate(updated_employee),
        timestamp=datetime.now().isoformat()
    )


# Endpoint to get the current token (for debugging)
@app.get("/current-token")
async def get_current_token(request: Request):
    """Get the current token from cookie or session"""
    token = request.cookies.get("access_token")
    session_token = None
    
    try:
        session_token = request.session.get("access_token")
    except Exception:
        pass
        
    return {
        "cookie_token": token,
        "session_token": session_token
    }

