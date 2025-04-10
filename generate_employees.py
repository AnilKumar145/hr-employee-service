from faker import Faker
import random
from datetime import date

fake = Faker()

roles = [
    "Developer", "Team Lead", "Project Manager", "HR Executive", "HR Manager",
    "Architect", "Delivery Manager", "COO", "CTO", "CEO",
    "Accounts Executive", "Accounts Manager", "Finance Manager", "CFO"
]

def generate_employee(emp_id):
    start_date = fake.date_between(start_date="-5y", end_date="today")
    is_active = random.choice([True, False])
    end_date = None if is_active else fake.date_between(start_date=start_date, end_date="today")

    return {
        "employee_id": f"EMP{1000 + emp_id}",
        "name": fake.name(),
        "date_of_birth": fake.date_of_birth(minimum_age=22, maximum_age=60),
        "gender": random.choice(["Male", "Female", "Other"]),
        "identification_no": fake.ssn() if random.choice(["SSN", "Aadhar"]) == "SSN" else str(fake.random_number(digits=12, fix_len=True)),
        "identification_type": random.choice(["Aadhar", "SSN"]),
        "address": fake.address().replace("\n", ", "),
        "current_work_location": fake.city() + " Tech Park",
        "role": random.choice(roles),
        "department": random.choice(["Engineering", "HR", "Sales", "Design", "Data"]),
        "salary": round(random.uniform(40000, 150000), 2),
        "system_assigned": random.choice([True, False]),
        "system_asset_id": fake.bothify(text="SYS-???-####") if random.choice([True, False]) else None,
        "is_active": is_active,
        "status": random.choice(["Employed", "Resigned", "Terminated"]),
        "start_date": start_date,
        "end_date": end_date,
        "employment_type": random.choice(["Permanent", "Contractor", "Intern"])
    }

def generate_employees(n=100):
    return [generate_employee(i) for i in range(1, n + 1)]
