from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import date

class IdentificationType(str, Enum):
    aadhar = "Aadhar"
    ssn = "SSN"

class StatusType(str, Enum):
    employed = "Employed"
    resigned = "Resigned"
    terminated = "Terminated"

class EmploymentType(str, Enum):
    permanent = "Permanent"
    contractor = "Contractor"
    intern = "Intern"

class RoleType(str, Enum):
    developer = "Developer"
    team_lead = "Team Lead"
    project_manager = "Project Manager"
    hr_executive = "HR Executive"
    hr_manager = "HR Manager"
    architect = "Architect"
    delivery_manager = "Delivery Manager"
    coo = "COO"
    cto = "CTO"
    ceo = "CEO"
    accounts_executive = "Accounts Executive"
    accounts_manager = "Accounts Manager"
    finance_manager = "Finance Manager"
    cfo = "CFO"

class Employee(BaseModel):
    employee_id: str
    name: str
    date_of_birth: date
    gender: str
    identification_no: str
    identification_type: IdentificationType
    address: str
    current_work_location: str
    role: RoleType
    department: str
    salary: float
    system_assigned: bool
    system_asset_id: Optional[str] = None
    is_active: bool
    status: StatusType
    start_date: date
    end_date: Optional[date] = None
    employment_type: EmploymentType
