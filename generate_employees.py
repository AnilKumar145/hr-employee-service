from faker import Faker
import random
from datetime import date

# Initialize Faker library for generating realistic fake data
fake = Faker()

# List of possible job roles in the organization
roles = [
    "Developer", "Team Lead", "Project Manager", "HR Executive", "HR Manager",
    "Architect", "Delivery Manager", "COO", "CTO", "CEO",
    "Accounts Executive", "Accounts Manager", "Finance Manager", "CFO"
]

def generate_employee(emp_id):
    """
    Generate a single employee with randomized attributes
    
    Args:
        emp_id (int): Sequential ID number to create unique employee ID
        
    Returns:
        dict: Dictionary containing all employee attributes
    """
    # Generate random start date within last 5 years
    start_date = fake.date_between(start_date="-5y", end_date="today")
    
    # Randomly determine if employee is active (using 1 for active, 0 for inactive)
    is_active = random.choice([1, 0])
    
    # If not active, generate end date after start date
    end_date = None if is_active == 1 else fake.date_between(start_date=start_date, end_date="today")
    
    # Generate first and last name separately
    first_name = fake.first_name()
    last_name = fake.last_name()
    
    # Generate employment status based on is_active
    status = random.choice(["Employed", "Resigned", "Terminated"])
    if is_active == 1:
        # Active employees can only be "Employed"
        status = "Employed"
        
    # Generate date of birth (as string)
    dob = fake.date_of_birth(minimum_age=22, maximum_age=60)
    dob_str = dob.strftime("%Y-%m-%d")

    # Return complete employee record as dictionary
    return {
        "employee_id": f"EMP{1000 + emp_id}",                           # Create sequential employee ID
        "first_name": first_name,                                       # First name
        "last_name": last_name,                                         # Last name
        "date_of_birth": dob_str,                                       # Random DOB for working age (as string)
        "gender": random.choice(["Male", "Female", "Other"]),           # Random gender
        "identification_no": fake.ssn() if random.choice(["SSN", "Aadhar"]) == "SSN" else str(fake.random_number(digits=12, fix_len=True)),  # ID number based on type
        "identification_type": random.choice(["Aadhar", "SSN"]),        # Random ID type
        
        # Separated address fields
        "street": fake.street_address(),                                # Street address
        "city": fake.city(),                                            # City
        "state": fake.state(),                                          # State/province
        "country": "USA",                                               # Country
        
        "current_work_location": fake.city() + " Tech Park",            # Random office location
        "role": random.choice(roles),                                   # Random job role
        "department": random.choice(["Engineering", "HR", "Sales", "Design", "Data"]),  # Random department
        "salary": round(random.uniform(40000, 150000), 2),              # Random salary between range
        "system_assigned": random.choice([True, False]),                # Random system assignment
        "system_asset_id": fake.bothify(text="SYS-???-####") if random.choice([True, False]) else None,  # Random asset ID if applicable
        "is_active": is_active,                                         # Active status (1=active, 0=inactive)
        "status": status,                                               # Employment status
        "start_date": start_date.strftime("%Y-%m-%d"),                  # Start date formatted as string
        "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,  # End date if applicable
        "employment_type": random.choice(["Permanent", "Contractor", "Intern"])  # Random employment type
    }

def generate_employees(n=100):
    """
    Generate a list of n random employees
    
    Args:
        n (int): Number of employees to generate, defaults to 100
        
    Returns:
        list: List of dictionaries containing employee data
    """
    return [generate_employee(i) for i in range(1, n + 1)]

# Function to save generated employees to a JSON file
def save_employees_to_json(employees, filename="sample_employees.json"):
    """
    Save generated employees to a JSON file
    
    Args:
        employees (list): List of employee dictionaries
        filename (str): Name of the output JSON file
    """
    import json
    from datetime import date
    
    # Custom JSON encoder to handle date objects
    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, date):
                return obj.strftime("%Y-%m-%d")
            return super().default(obj)
    
    with open(filename, "w") as f:
        json.dump(employees, f, indent=2, cls=DateEncoder)

# Generate and save new sample data when run directly
if __name__ == "__main__":
    print("Generating new sample employee data...")
    employees = generate_employees(100)
    save_employees_to_json(employees)
    print(f"Generated {len(employees)} employees and saved to sample_employees.json")
