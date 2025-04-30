
from typing import List, Optional
import json
import os
from fastapi import FastAPI, Depends, HTTPException, status, Security, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
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

# Initialize FastAPI app with Swagger UI configuration
app = FastAPI(
    title="HR Employee Service",
    description="API for HR employee management",
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
@app.get("/employees/", response_model=List[dict])
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
    return employees

# Get a specific employee by ID
@app.get("/employees/{employee_id}", response_model=dict)
async def read_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a specific employee by ID"""
    employee = get_employee_by_id(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# Create a new employee
@app.post("/employees/", response_model=dict)
async def create_new_employee(
    employee: dict,
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new employee"""
    return create_employee(employee)

# Update an existing employee
@app.put("/employees/{employee_id}", response_model=dict)
async def update_existing_employee(
    employee_id: str,
    employee: dict,
    current_user: User = Depends(get_current_user_from_token)
):
    """Update an existing employee"""
    updated_employee = update_employee(employee_id, employee)
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated_employee

# Delete an employee
@app.delete("/employees/{employee_id}", response_model=dict)
async def delete_existing_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete an employee"""
    success = delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": f"Employee {employee_id} deleted successfully"}

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
