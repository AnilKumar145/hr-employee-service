from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from datetime import date

# Enum for identification document types
class IdentificationType(str, Enum):
    aadhar = "Aadhar"  # Indian national ID
    ssn = "SSN"        # US Social Security Number

# Enum for employee status types
class StatusType(str, Enum):
    employed = "Employed"    # Currently working
    resigned = "Resigned"    # Left voluntarily
    terminated = "Terminated"  # Employment ended by company

# Enum for types of employment contracts
class EmploymentType(str, Enum):
    permanent = "Permanent"   # Full-time permanent employee
    contractor = "Contractor"  # External contractor
    intern = "Intern"         # Temporary internship position

# Enum for job roles within the organization
class RoleType(str, Enum):
    developer = "Developer"
    team_lead = "Team Lead"
    project_manager = "Project Manager"
    hr_executive = "HR Executive"
    hr_manager = "HR Manager"
    architect = "Architect"
    delivery_manager = "Delivery Manager"
    coo = "COO"               # Chief Operating Officer
    cto = "CTO"               # Chief Technology Officer
    ceo = "CEO"               # Chief Executive Officer
    accounts_executive = "Accounts Executive"
    accounts_manager = "Accounts Manager"
    finance_manager = "Finance Manager"
    cfo = "CFO"               # Chief Financial Officer

# Main Employee data model - Updated with requested changes
class Employee(BaseModel):
    employee_id: str                          # Unique identifier for employee
    first_name: str                           # First name of employee
    last_name: str                            # Last name of employee
    date_of_birth: date                       # Birth date for age calculation
    gender: str                               # Gender identity
    identification_no: str                    # ID document number (SSN/Aadhar)
    identification_type: IdentificationType   # Type of ID document
    
    # Address fields - separated as requested
    street: str                               # Street address
    city: str                                 # City
    state: str                                # State/province
    country: str                              # Country
    
    current_work_location: str                # Office location
    role: RoleType                            # Job role/title
    department: str                           # Department (Engineering, HR, etc.)
    salary: float                             # Annual salary amount
    system_assigned: bool                     # Whether employee has company system
    system_asset_id: Optional[str] = None     # Asset ID of assigned system if any
    is_active: Literal[0, 1] = 1              # Whether employee is active: 1=active, 0=inactive
    status: StatusType                        # Current employment status
    start_date: date                          # Employment start date
    end_date: Optional[date] = None           # Employment end date if applicable
    employment_type: EmploymentType           # Type of employment contract
