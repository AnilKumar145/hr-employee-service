from generate_employees import generate_employees, save_employees_to_json
import os

# Delete existing sample data file if it exists
if os.path.exists("sample_employees.json"):
    os.remove("sample_employees.json")
    print("Removed existing sample_employees.json file")

# Generate new sample data
print("Generating new sample employee data...")
employees = generate_employees(100)
save_employees_to_json(employees)
print(f"Generated {len(employees)} employees and saved to sample_employees.json")