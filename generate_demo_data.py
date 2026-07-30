#!/usr/bin/env python3
"""
Synthetic HR Data Generator for People Chat Demo
Generates realistic employee, job catalog, and reporting structure data
matching a real-world HR schema. Company: The Guild (fantasy-themed).

Outputs 4 CSV files into people_chat/data/sample/
"""

import csv
import random
import string
from datetime import datetime, timedelta, date
from pathlib import Path
import hashlib

random.seed(42)

# ─── Company Info ────────────────────────────────────────

COMPANY_NAME = "The Guild"
COMPANY_DOMAIN = "theguild.com"

# ─── Divisions, Departments, and Job Families ────────────

DIVISIONS_DEPARTMENTS = {
    "Engineering & Technology": {
        "departments": [
            "Software Engineering", "DevOps & Infrastructure", "Quality Assurance",
            "Security", "Data Engineering", "AI & Machine Learning", "Platform Engineering",
            "IT", "Architecture"
        ],
        "lead": "CTO"
    },
    "Product": {
        "departments": [
            "Product Management", "Product Design", "UX Research", "Product Operations"
        ],
        "lead": "CPO"
    },
    "Sales & Revenue": {
        "departments": [
            "Enterprise Sales", "Mid-Market Sales", "SMB Sales", "Sales Development",
            "Sales Operations", "Revenue Operations", "Channel & Partnerships",
            "Account Management"
        ],
        "lead": "CRO"
    },
    "Marketing": {
        "departments": [
            "Demand Generation", "Brand Marketing", "Content Marketing",
            "Product Marketing", "Marketing Operations", "Events & Community",
            "Sales Enablement", "Corporate Communications"
        ],
        "lead": "CMO"
    },
    "Customer Success": {
        "departments": [
            "Customer Success Management", "Customer Support", "Implementation & Onboarding",
            "Professional Services", "Solutions Engineering", "Renewals"
        ],
        "lead": "VP Customer Success"
    },
    "G&A": {
        "departments": [
            "Finance", "Legal", "People & HR", "Talent Acquisition",
            "Facilities & Admin", "Procurement", "Payroll", "Compliance"
        ],
        "lead": "CFO"
    },
    "Operations": {
        "departments": [
            "Business Operations", "Corporate Strategy", "Data Analytics & Insights",
            "FP&A", "Program Management"
        ],
        "lead": "COO"
    }
}

JOB_FAMILIES = [
    "Engineering", "Design", "Product Management", "Data & Analytics",
    "Marketing", "Sales", "Customer Success", "Finance", "Legal",
    "Human Resources", "Operations", "Security", "IT", "Administrative"
]

# ─── Radford Level → Job Title Mappings ───────────────────

RADFORD_IC_TITLES = {
    "Engineering": {
        "P1": "Junior Software Engineer", "P2": "Software Engineer",
        "P3": "Senior Software Engineer", "P4": "Staff Software Engineer",
        "P5": "Principal Software Engineer", "P6": "Distinguished Engineer"
    },
    "Design": {
        "P1": "Junior Designer", "P2": "Designer",
        "P3": "Senior Designer", "P4": "Staff Designer",
        "P5": "Principal Designer", "P6": "Distinguished Designer"
    },
    "Product Management": {
        "P1": "Associate Product Manager", "P2": "Product Manager",
        "P3": "Senior Product Manager", "P4": "Staff Product Manager",
        "P5": "Principal Product Manager", "P6": "Distinguished PM"
    },
    "Data & Analytics": {
        "P1": "Junior Data Analyst", "P2": "Data Analyst",
        "P3": "Senior Data Analyst", "P4": "Lead Data Analyst",
        "P5": "Principal Data Scientist", "P6": "Distinguished Data Scientist"
    },
    "Marketing": {
        "P1": "Marketing Coordinator", "P2": "Marketing Specialist",
        "P3": "Senior Marketing Manager", "P4": "Associate Director of Marketing",
        "P5": "Director of Marketing", "P6": "Senior Director of Marketing"
    },
    "Sales": {
        "P1": "Sales Development Representative", "P2": "Account Executive",
        "P3": "Senior Account Executive", "P4": "Enterprise Account Executive",
        "P5": "Principal Account Executive", "P6": "Strategic Account Executive"
    },
    "Finance": {
        "P1": "Finance Associate", "P2": "Financial Analyst",
        "P3": "Senior Financial Analyst", "P4": "Finance Manager",
        "P5": "Senior Finance Manager", "P6": "Director of Finance"
    },
    "Human Resources": {
        "P1": "HR Coordinator", "P2": "HR Generalist",
        "P3": "Senior HR Business Partner", "P4": "HRBP Lead",
        "P5": "Principal People Partner", "P6": "Director of People"
    },
    "Customer Success": {
        "P1": "Customer Success Associate", "P2": "Customer Success Manager",
        "P3": "Senior Customer Success Manager", "P4": "CS Team Lead",
        "P5": "Principal CS Manager", "P6": "Director of Customer Success"
    },
    "Operations": {
        "P1": "Operations Associate", "P2": "Operations Analyst",
        "P3": "Senior Operations Analyst", "P4": "Operations Manager",
        "P5": "Senior Operations Manager", "P6": "Director of Operations"
    },
    "Security": {
        "P1": "Security Analyst I", "P2": "Security Analyst II",
        "P3": "Senior Security Analyst", "P4": "Security Engineer",
        "P5": "Principal Security Engineer", "P6": "Director of Security"
    },
    "IT": {
        "P1": "IT Support Associate", "P2": "IT Support Specialist",
        "P3": "Senior IT Specialist", "P4": "IT Lead",
        "P5": "Principal IT Manager", "P6": "Director of IT"
    }
}

# Support track (S1-S5)
SUPPORT_TITLES = {
    "S1": "Intern", "S2": "Associate", "S3": "Specialist",
    "S4": "Senior Specialist", "S5": "Lead"
}

# Management track (M1-M6)
MANAGEMENT_TITLES = {
    "Engineering": {
        "M1": "Engineering Manager", "M2": "Senior Engineering Manager",
        "M3": "Director of Engineering", "M4": "Senior Director of Engineering",
        "M5": "VP of Engineering", "M6": "SVP of Engineering"
    },
    "Product": {
        "M1": "Product Manager Lead", "M2": "Senior Product Manager Lead",
        "M3": "Director of Product", "M4": "Senior Director of Product",
        "M5": "VP of Product", "M6": "SVP of Product"
    },
    "Sales": {
        "M1": "Sales Manager", "M2": "Senior Sales Manager",
        "M3": "Director of Sales", "M4": "Senior Director of Sales",
        "M5": "VP of Sales", "M6": "SVP of Sales"
    },
    "Marketing": {
        "M1": "Marketing Manager", "M2": "Senior Marketing Manager",
        "M3": "Director of Marketing", "M4": "Senior Director of Marketing",
        "M5": "VP of Marketing", "M6": "SVP of Marketing"
    },
    "Finance": {
        "M1": "Finance Manager", "M2": "Senior Finance Manager",
        "M3": "Director of Finance", "M4": "Senior Director of Finance",
        "M5": "VP of Finance", "M6": "SVP of Finance"
    },
    "Human Resources": {
        "M1": "HR Manager", "M2": "Senior HR Manager",
        "M3": "Director of People", "M4": "Senior Director of People",
        "M5": "VP of People", "M6": "SVP of People"
    },
    "Customer Success": {
        "M1": "CS Manager", "M2": "Senior CS Manager",
        "M3": "Director of Customer Success", "M4": "Senior Director of CS",
        "M5": "VP of Customer Success", "M6": "SVP of Customer Success"
    },
    "Operations": {
        "M1": "Operations Manager", "M2": "Senior Ops Manager",
        "M3": "Director of Operations", "M4": "Senior Director of Ops",
        "M5": "VP of Operations", "M6": "SVP of Operations"
    },
    "Data & Analytics": {
        "M1": "Analytics Manager", "M2": "Senior Analytics Manager",
        "M3": "Director of Analytics", "M4": "Senior Director of Analytics",
        "M5": "VP of Data", "M6": "SVP of Data"
    },
    "Design": {
        "M1": "Design Manager", "M2": "Senior Design Manager",
        "M3": "Director of Design", "M4": "Senior Director of Design",
        "M5": "VP of Design", "M6": "SVP of Design"
    },
    "IT": {
        "M1": "IT Manager", "M2": "Senior IT Manager",
        "M3": "Director of IT", "M4": "Senior Director of IT",
        "M5": "VP of IT", "M6": "SVP of IT"
    }
}

# Executive track (E1-E6)
EXECUTIVE_TITLES = {
    "E1": "VP", "E2": "Senior VP", "E3": "Executive VP",
    "E4": "Senior EVP", "E5": "Chief Officer", "E6": "CEO"
}

# ─── Salary Ranges (US Tech, annual base) ────────────────

SALARY_RANGES = {
    "S1": (30000, 45000), "S2": (38000, 55000), "S3": (45000, 70000),
    "S4": (55000, 85000), "S5": (70000, 100000),
    "P1": (55000, 85000), "P2": (80000, 120000), "P3": (105000, 150000),
    "P4": (135000, 185000), "P5": (170000, 240000), "P6": (210000, 320000),
    "M1": (120000, 170000), "M2": (150000, 210000), "M3": (175000, 250000),
    "M4": (210000, 300000), "M5": (260000, 420000), "M6": (350000, 600000),
    "E1": (300000, 500000), "E2": (400000, 700000), "E3": (500000, 900000),
    "E4": (600000, 1200000), "E5": (800000, 2000000), "E6": (1500000, 5000000)
}

# ─── First/Last Name Banks ───────────────────────────────

FIRST_NAMES = [
    "Alex", "Jordan", "Morgan", "Taylor", "Casey", "Riley", "Avery", "Quinn",
    "James", "Sarah", "Michael", "Emily", "David", "Jessica", "Daniel", "Ashley",
    "Chris", "Amanda", "Matt", "Stephanie", "Ryan", "Lauren", "Andrew", "Rachel",
    "Kevin", "Megan", "Brian", "Nicole", "Jason", "Samantha", "Tyler", "Kayla",
    "Jake", "Hannah", "Sam", "Olivia", "Ben", "Emma", "Will", "Aria",
    "Nate", "Ella", "Luke", "Mia", "Dylan", "Lily", "Ethan", "Chloe",
    "Noah", "Zoe", "Liam", "Nora", "Owen", "Luna", "Miles", "Stella",
    "Kai", "Aurora", "Ezra", "Hazel", "Leo", "Ivy", "Cole", "Violet",
    "Finn", "Aria", "Wren", "Isla", "Reid", "June", "Jade", "Sage",
    "Blake", "Bryn", "Ash", "Peyton", "Rowan", "Drew", "Skyler", "Emerson"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Hill",
    "Green", "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Roberts",
    "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins",
    "Stewart", "Morris", "Nguyen", "Murphy", "Rivera", "Cook", "Rogers", "Morgan"
]

CITIES = [
    ("San Francisco", "CA", "94101"), ("San Jose", "CA", "95101"),
    ("Austin", "TX", "73301"), ("Seattle", "WA", "98101"),
    ("New York", "NY", "10001"), ("Boston", "MA", "02101"),
    ("Denver", "CO", "80201"), ("Chicago", "IL", "60601"),
    ("Portland", "OR", "97201"), ("Salt Lake City", "UT", "84101"),
    ("Los Angeles", "CA", "90001"), ("Atlanta", "GA", "30301"),
    ("Dallas", "TX", "75201"), ("Phoenix", "AZ", "85001"),
    ("Minneapolis", "MN", "55401"), ("Raleigh", "NC", "27601"),
    ("Boulder", "CO", "80301"), ("Lehi", "UT", "84043"),
    ("Provo", "UT", "84601"), ("Boise", "ID", "83701")
]

EMPLOYMENT_STATUSES = ["Active", "Active", "Active", "Active", "Active", "Active", "Active",
                       "Terminated", "Contractor", "Leave of Absence", "Part Time", "Seasonal"]

BONUS_TYPES = ["Annual Bonus", "Annual Bonus", "Annual Bonus", "Commission", "Commission", "No Bonus"]

# ─── Helper Functions ─────────────────────────────────────

def generate_employee_id(index):
    return f"EMP{index:05d}"

def generate_email(first, last):
    return f"{first.lower()}.{last.lower()}@{COMPANY_DOMAIN}"

def weighted_choice(items, weights=None):
    return random.choices(items, weights=weights, k=1)[0]

def random_date(start_year, end_year):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def salary_for_level(level):
    lo, hi = SALARY_RANGES[level]
    return random.randint(lo, hi)

def radford_to_index(level):
    """Convert Radford level to numeric for comparison."""
    track = level[0]  # S, P, M, E
    num = int(level[1])
    track_order = {'S': 0, 'P': 1, 'M': 2, 'E': 3}
    return track_order[track] * 10 + num

# ─── Generate Job Catalog ─────────────────────────────────

def generate_job_catalog():
    jobs = []
    job_code = 100
    
    all_divisions = list(DIVISIONS_DEPARTMENTS.keys())
    
    for family in JOB_FAMILIES:
        # Skip Admin - just use support levels
        if family == "Administrative":
            continue
        
        # Determine what Radford levels this family gets
        if family in ("IT", "Administrative"):
            levels = [f"S{i}" for i in range(1, 6)] + [f"P{i}" for i in range(1, 4)]
            mgmt_levels = ["M1", "M2", "M3"]
        elif family in ("Security",):
            levels = [f"P{i}" for i in range(1, 6)]
            mgmt_levels = ["M1", "M2", "M3", "M4"]
        elif family in ("Data & Analytics",):
            levels = [f"P{i}" for i in range(1, 7)]
            mgmt_levels = ["M1", "M2", "M3", "M4"]
        else:
            levels = [f"P{i}" for i in range(1, 6)]
            mgmt_levels = ["M1", "M2", "M3"]
        
        # Assign a division
        if family == "Engineering":
            division = "Engineering & Technology"
        elif family == "Design":
            division = "Product"
        elif family == "Product Management":
            division = "Product"
        elif family == "Data & Analytics":
            division = "Operations"
        elif family == "Marketing":
            division = "Marketing"
        elif family == "Sales":
            division = "Sales & Revenue"
        elif family == "Customer Success":
            division = "Customer Success"
        elif family == "Finance":
            division = "G&A"
        elif family == "Legal":
            division = "G&A"
        elif family == "Human Resources":
            division = "G&A"
        elif family == "Operations":
            division = "Operations"
        elif family == "Security":
            division = "Engineering & Technology"
        elif family == "IT":
            division = "Engineering & Technology"
        else:
            division = random.choice(all_divisions)
        
        dept = random.choice(DIVISIONS_DEPARTMENTS[division]["departments"])
        
        # Add IC roles
        for level in levels:
            level_num = int(level[1])
            if family in RADFORD_IC_TITLES and level in RADFORD_IC_TITLES[family]:
                title = RADFORD_IC_TITLES[family][level]
            else:
                title = f"{level} - {family}"
            
            salary_lo, salary_hi = SALARY_RANGES[level]
            mid = (salary_lo + salary_hi) // 2
            min_salary = salary_lo
            max_salary = salary_hi
            
            # Determine job family
            job_family = family
            
            jobs.append({
                "Job Code": job_code,
                "Position Title": title,
                "Department": dept,
                "Division": division,
                "Job Family": job_family,
                "Active or Inactive": "Active",
                "Radford Level": level,
                "Benchmarking Code One": "",
                "Benchmarking One Percentage": "",
                "Benchmarking Code Two": "",
                "Benchmarking Two Percentage": "",
                "Band Number": level_num,
                "Range Min": min_salary,
                "Quartile One Top": (min_salary + mid) // 2,
                "Mid": mid,
                "Quartile Three Top": (mid + max_salary) // 2,
                "Max": max_salary,
                "Set Rate": "",
                "AIP or Commissions": random.choice(["AIP", "AIP", "Commissions", "None", "None"]),
                "AIP Percentage": random.choice([5, 5, 10, 10, 15, 20, 0]),
                "Commissions": random.choice([0, 0, 0, 5000, 10000, 25000]) if family == "Sales" else 0,
                "Hourly or Salary": "Salary",
                "Exemption Status": random.choice(["Exempt", "Exempt", "Exempt", "Non-Exempt"]),
                "EEOC Category": random.choice(["Professionals", "Technicians", "Sales Workers",
                                                 "Office & Clerical", "Executives"]),
                "Job Description Link": f"https://internal.{COMPANY_DOMAIN}/jobs/{job_code}",
                "Equity Structure": random.choice(["", "", "Options", "Options", "Options", "RSU", "RSU"])
            })
            job_code += 1
        
        # Add management roles
        for level in mgmt_levels:
            level_num = int(level[1])
            
            # Map family to management title key
            mgmt_key = family
            if mgmt_key not in MANAGEMENT_TITLES:
                mgmt_key = "Operations"
            
            if level in MANAGEMENT_TITLES[mgmt_key]:
                title = MANAGEMENT_TITLES[mgmt_key][level]
            else:
                title = f"{level} Manager - {family}"
            
            salary_lo, salary_hi = SALARY_RANGES[level]
            mid = (salary_lo + salary_hi) // 2
            
            jobs.append({
                "Job Code": job_code,
                "Position Title": title,
                "Department": dept,
                "Division": division,
                "Job Family": job_family if 'job_family' in dir() else family,
                "Active or Inactive": "Active",
                "Radford Level": level,
                "Benchmarking Code One": "",
                "Benchmarking One Percentage": "",
                "Benchmarking Code Two": "",
                "Benchmarking Two Percentage": "",
                "Band Number": level_num,
                "Range Min": salary_lo,
                "Quartile One Top": (salary_lo + mid) // 2,
                "Mid": mid,
                "Quartile Three Top": (mid + salary_hi) // 2,
                "Max": salary_hi,
                "Set Rate": "",
                "AIP or Commissions": "AIP",
                "AIP Percentage": random.choice([10, 15, 20, 25, 30]),
                "Commissions": 0,
                "Hourly or Salary": "Salary",
                "Exemption Status": "Exempt",
                "EEOC Category": "Executives",
                "Job Description Link": f"https://internal.{COMPANY_DOMAIN}/jobs/{job_code}",
                "Equity Structure": random.choice(["Options", "Options", "RSU", "RSU", "RSU"])
            })
            job_code += 1
    
    # Add a few executive roles
    exec_divisions = [("Operations", "Corporate Strategy"), ("G&A", "Finance"), ("G&A", "Legal"), ("Engineering & Technology", "Architecture"),
                      ("Marketing", "Corporate Communications"), ("Sales & Revenue", "Revenue Operations"),
                      ("Operations", "Corporate Strategy")]
    for i, (div, dept) in enumerate(exec_divisions):
        assign_level = "E6" if i == 0 else f"E{i}"  # CEO gets E6, rest cascade E1-E5
        level = assign_level
        title = EXECUTIVE_TITLES.get(level, "Chief Officer")
        if i == 0:
            title = "CEO"
        elif i == 1:
            title = "CFO"
        elif i == 2:
            title = "General Counsel"
        elif i == 3:
            title = "CTO"
        elif i == 4:
            title = "CMO"
        elif i == 5:
            title = "CRO"
        elif i == 6:
            title = "COO"
        
        salary_lo, salary_hi = SALARY_RANGES[level]
        mid = (salary_lo + salary_hi) // 2
        
        jobs.append({
            "Job Code": job_code,
            "Position Title": title,
            "Department": dept,
            "Division": div,
            "Job Family": "Executive",
            "Active or Inactive": "Active",
            "Radford Level": level,
            "Benchmarking Code One": "",
            "Benchmarking One Percentage": "",
            "Benchmarking Code Two": "",
            "Benchmarking Two Percentage": "",
            "Band Number": int(level[1]) if len(level) > 1 else 6,
            "Range Min": salary_lo,
            "Quartile One Top": (salary_lo + mid) // 2,
            "Mid": mid,
            "Quartile Three Top": (mid + salary_hi) // 2,
            "Max": salary_hi,
            "Set Rate": "",
            "AIP or Commissions": "AIP",
            "AIP Percentage": random.choice([25, 30, 40, 50]),
            "Commissions": 0,
            "Hourly or Salary": "Salary",
            "Exemption Status": "Exempt",
            "EEOC Category": "Executives",
            "Job Description Link": f"https://internal.{COMPANY_DOMAIN}/jobs/{job_code}",
            "Equity Structure": "RSU"
        })
        job_code += 1
    
    return jobs


# ─── Generate Employees ──────────────────────────────────

def generate_employees(job_catalog, num_employees=750):
    employees = []
    
    # Filter job catalog to actual employee-worthy roles (not all catalog entries)
    employee_jobs = [j for j in job_catalog if "Intern" not in j["Position Title"]]
    
    # Pick a CEO
    ceo = {
        "Employee #": "EMP00001",
        "First Name": "Alistair",
        "Preferred Name": "",
        "Last Name": "Ironwood",
        "First Name Last Name": "Alistair Ironwood",
        "Job Title": "CEO",
        "Department": "Corporate Strategy",
        "Division": "Operations",
        "Reporting to": "",
        "Hire Date": date(2015, 3, 1),
        "Work Email": "alistair.ironwood@theguild.com",
        "Birth Date": date(1975, 6, 15),
        "Gender": "Male",
        "Employment Status": "Active",
        "City": "Salt Lake City",
        "State": "UT",
        "Zip Code": "84101",
        "Compensation: Date": date(2026, 1, 1),
        "Pay rate": 1500000,
        "Time Type": "Salary",
        "Exempt": "Exempt",
        "Pay Schedule": "Monthly",
        "Termination Date": "",
        "Radford Level": "E6",
        "Bonus Type": "Annual Bonus",
        "Bonus Amount": 3000000,
        "EEID": "EEID00001",
        # Current Team fields
        "People Leader?": "Yes",
        "Annualized Pay": 1500000,
        "Annual Pay": 1500000,
        "Director": "",
        "E-1": "",
        "First Executive": "",
        "Top Executive": "",
        "Skip Level Manager": "",
        "HRBP": "Emily Stone",
        "July Threshold": 150000,
        "Jan Threshold": 150000,
        "Job Code": next(j["Job Code"] for j in job_catalog if j["Position Title"] == "CEO"),
        "Band Number": 6,
        "Min": 1500000,
        "25% RP": 2000000,
        "Mid": 2500000,
        "75% RP": 3000000,
        "Max": 5000000,
        "RP %": 60.0
    }
    employees.append(ceo)
    
    # C-suite
    exec_team = {
        "CFO": "EMP00002", "CTO": "EMP00003", "CMO": "EMP00004",
        "CRO": "EMP00005", "COO": "EMP00006", "General Counsel": "EMP00007"
    }
    exec_names = {
        "CFO": ("Meredith", "Kingsley"), "CTO": ("Dorian", "Blackthorn"),
        "CMO": ("Seraphina", "Ravenscroft"), "CRO": ("Thorne", "Ashford"),
        "COO": ("Gideon", "Stonewall"), "General Counsel": ("Eleanor", "Whitmore")
    }
    
    for i, (title, emp_id) in enumerate(exec_team.items()):
        first, last = exec_names[title]
        job = next((j for j in job_catalog if j["Position Title"] == title), job_catalog[0])
        level = f"E{6 - len(exec_team) + i + 1}"  # E2-E3 range (second tier execs)
        salary = salary_for_level(level)
        
        emp = {
            "Employee #": emp_id,
            "First Name": first,
            "Preferred Name": "",
            "Last Name": last,
            "First Name Last Name": f"{first} {last}",
            "Job Title": title,
            "Department": job["Department"],
            "Division": job["Division"],
            "Reporting to": "EMP00001",
            "Hire Date": random_date(2016, 2019),
            "Work Email": generate_email(first, last),
            "Birth Date": random_date(1970, 1985),
            "Gender": random.choice(["Male", "Female", "Female", "Male"]),
            "Employment Status": "Active",
            "City": random.choice(["Salt Lake City", "San Francisco", "New York", "Austin"]),
            "State": random.choice(["UT", "CA", "NY", "TX"]),
            "Zip Code": "84101",
            "Compensation: Date": date(2026, 1, 1),
            "Pay rate": salary,
            "Time Type": "Salary",
            "Exempt": "Exempt",
            "Pay Schedule": "Monthly",
            "Termination Date": "",
            "Radford Level": level,
            "Bonus Type": "Annual Bonus",
            "Bonus Amount": int(salary * random.choice([0.3, 0.4, 0.5, 0.6])),
            "EEID": f"EEID{i+2:05d}",
            "People Leader?": "Yes",
            "Annualized Pay": salary,
            "Annual Pay": salary,
            "Director": "",
            "E-1": "",
            "First Executive": "",
            "Top Executive": "",
            "Skip Level Manager": "",
            "HRBP": "Emily Stone",
            "July Threshold": int(salary * 0.1),
            "Jan Threshold": int(salary * 0.1),
            "Job Code": job["Job Code"],
            "Band Number": job["Band Number"],
            "Min": job["Range Min"],
            "25% RP": job["Quartile One Top"],
            "Mid": job["Mid"],
            "75% RP": job["Quartile Three Top"],
            "Max": job["Max"],
            "RP %": round((salary / job["Mid"]) * 100, 1)
        }
        employees.append(emp)
    
    # Generate remaining employees
    current_id = 8  # Start after CEO + 6 execs
    employee_count = current_id
    
    # Division heads (directors - M3/M4 level)
    division_heads = {}
    for div_name in DIVISIONS_DEPARTMENTS.keys():
        emp_id = f"EMP{current_id:05d}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        division = DIVISIONS_DEPARTMENTS[div_name]
        dept = division["departments"][0]
        
        job = next((j for j in job_catalog if j["Division"] == div_name and "Director" in j["Position Title"] and j["Radford Level"][0] == "M"), None)
        if not job:
            job = next((j for j in job_catalog if j["Division"] == div_name and "Director" in j["Position Title"]), None)
        
        title = job["Position Title"] if job else f"Director of {div_name}"
        level = "M3" if not job else job["Radford Level"]
        salary = salary_for_level(level)
        
        emp = {
            "Employee #": emp_id,
            "First Name": first,
            "Preferred Name": "",
            "Last Name": last,
            "First Name Last Name": f"{first} {last}",
            "Job Title": title,
            "Department": dept,
            "Division": div_name,
            "Reporting to": random.choice(["EMP00001", "EMP00002", "EMP00003", "EMP00005"]),
            "Hire Date": random_date(2017, 2021),
            "Work Email": generate_email(first, last),
            "Birth Date": random_date(1978, 1990),
            "Gender": random.choice(["Male", "Female"]),
            "Employment Status": "Active",
            "City": random.choice(["Salt Lake City", "San Francisco", "Austin", "Denver", "Seattle"]),
            "State": random.choice(["UT", "CA", "TX", "CO", "WA"]),
            "Zip Code": "84101",
            "Compensation: Date": date(2026, 1, 1),
            "Pay rate": salary,
            "Time Type": "Salary",
            "Exempt": "Exempt",
            "Pay Schedule": "Monthly",
            "Termination Date": "",
            "Radford Level": level,
            "Bonus Type": random.choice(["Annual Bonus", "Annual Bonus", "Annual Bonus", "Commission"]),
            "Bonus Amount": int(salary * random.choice([0.05, 0.1, 0.15, 0.2])),
            "EEID": f"EEID{current_id:05d}",
            "People Leader?": "Yes",
            "Annualized Pay": salary,
            "Annual Pay": salary,
            "Director": emp_id,
            "E-1": "",
            "First Executive": "",
            "Top Executive": "",
            "Skip Level Manager": "",
            "HRBP": random.choice(["Emily Stone", "Marcus Webb", "Priya Patel"]),
            "July Threshold": int(salary * 0.1),
            "Jan Threshold": int(salary * 0.1),
            "Job Code": job["Job Code"] if job else 100,
            "Band Number": int(level[1]) if len(level) > 1 else 3,
            "Min": job["Range Min"] if job else salary - 30000,
            "25% RP": job["Quartile One Top"] if job else salary - 10000,
            "Mid": job["Mid"] if job else salary,
            "75% RP": job["Quartile Three Top"] if job else salary + 10000,
            "Max": job["Max"] if job else salary + 30000,
            "RP %": round((salary / (job["Mid"] if job else salary)) * 100, 1)
        }
        division_heads[div_name] = emp_id
        employees.append(emp)
        current_id += 1
        employee_count += 1
    
    # Middle managers (M1-M2) and ICs
    manager_pool = list(division_heads.values())
    
    for _ in range(current_id, num_employees + 1):
        emp_id = f"EMP{current_id:05d}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        
        div_name = random.choice(list(DIVISIONS_DEPARTMENTS.keys()))
        division = DIVISIONS_DEPARTMENTS[div_name]
        dept = random.choice(division["departments"])
        
        # Determine role level
        roll = random.random()
        is_manager = roll < 0.15  # 15% are managers
        
        if is_manager:
            level = random.choice(["M1", "M2"])
        else:
            level = random.choice(["P1", "P2", "P3", "P4"])
        
        # Determine family from division
        div_to_family = {
            "Engineering & Technology": "Engineering",
            "Product": "Product Management",
            "Sales & Revenue": "Sales",
            "Marketing": "Marketing",
            "Customer Success": "Customer Success",
            "G&A": random.choice(["Finance", "Human Resources"]),
            "Operations": "Operations"
        }
        family = div_to_family.get(div_name, "Operations")
        
        # Find matching job from catalog
        matching_jobs = [j for j in job_catalog if j["Department"] == dept and j["Radford Level"] == level]
        if not matching_jobs:
            matching_jobs = [j for j in job_catalog if j["Division"] == div_name and j["Radford Level"] == level]
        if not matching_jobs:
            matching_jobs = [j for j in job_catalog if j["Radford Level"] == level]
        
        job = random.choice(matching_jobs) if matching_jobs else None
        
        title = job["Position Title"] if job else f"{level} - {family}"
        
        # IC title lookup
        if not is_manager and family in RADFORD_IC_TITLES and level in RADFORD_IC_TITLES[family]:
            title = RADFORD_IC_TITLES[family][level]
        elif is_manager:
            mgmt_family = family
            if mgmt_family in MANAGEMENT_TITLES and level in MANAGEMENT_TITLES[mgmt_family]:
                title = MANAGEMENT_TITLES[mgmt_family][level]
        
        salary = salary_for_level(level)
        
        # Determine reporting structure
        if level in ("M1", "M2"):
            reporting_to = division_heads.get(div_name, random.choice(manager_pool))
            manager_pool.append(emp_id)
        else:
            reporting_to = random.choice(manager_pool) if manager_pool else "EMP00001"
        
        # Employment status
        status = random.choices(
            ["Active", "Terminated", "Contractor", "Leave of Absence", "Part Time"],
            weights=[70, 5, 3, 1, 1], k=1
        )[0]
        
        term_date = ""
        if status == "Terminated":
            term_date = str(random_date(2023, 2026))
        
        city_info = random.choice(CITIES)
        
        time_type = random.choice(["Salary", "Salary", "Salary", "Hourly"])
        exempt = "Exempt" if level[0] in ("M", "E") or level in ("P3", "P4", "P5", "P6") else random.choice(["Exempt", "Non-Exempt"])
        pay_schedule = random.choice(["Monthly", "Bi-Weekly", "Bi-Weekly", "Twice a Month"])
        
        bonus_type = random.choice(BONUS_TYPES)
        bonus_amt = 0
        if bonus_type == "Annual Bonus":
            bonus_amt = int(salary * random.choice([0.03, 0.05, 0.08, 0.1, 0.15]))
        elif bonus_type == "Commission":
            bonus_amt = int(salary * random.choice([0.1, 0.2, 0.3]))
        
        hire_date = random_date(2018, 2025)
        
        emp = {
            "Employee #": emp_id,
            "First Name": first,
            "Preferred Name": "",
            "Last Name": last,
            "First Name Last Name": f"{first} {last}",
            "Job Title": title,
            "Department": dept,
            "Division": div_name,
            "Reporting to": reporting_to,
            "Hire Date": str(hire_date),
            "Work Email": generate_email(first, last),
            "Birth Date": str(random_date(1975, 2000)),
            "Gender": random.choice(["Male", "Female", "Non-Binary", ""]),
            "Employment Status": status,
            "City": city_info[0],
            "State": city_info[1],
            "Zip Code": city_info[2],
            "Compensation: Date": str(date(2026, 1, 1)),
            "Pay rate": salary,
            "Time Type": time_type,
            "Exempt": exempt,
            "Pay Schedule": pay_schedule,
            "Termination Date": term_date,
            "Radford Level": level,
            "Bonus Type": bonus_type,
            "Bonus Amount": bonus_amt,
            "EEID": f"EEID{current_id:05d}",
            "People Leader?": "Yes" if is_manager else "No",
            "Annualized Pay": int(salary * (1 + (bonus_amt / salary if bonus_amt > 0 else 0))),
            "Annual Pay": salary,
            "Director": "",
            "E-1": "",
            "First Executive": "",
            "Top Executive": "",
            "Skip Level Manager": "",
            "HRBP": random.choice(["Emily Stone", "Marcus Webb", "Priya Patel", "Jordan Kim"]),
            "July Threshold": int(salary * 0.1),
            "Jan Threshold": int(salary * 0.1),
            "Job Code": job["Job Code"] if job else 100,
            "Band Number": int(level[1]) if len(level) > 1 else 1,
            "Min": job["Range Min"] if job else salary - 15000,
            "25% RP": job["Quartile One Top"] if job else salary - 5000,
            "Mid": job["Mid"] if job else salary,
            "75% RP": job["Quartile Three Top"] if job else salary + 5000,
            "Max": job["Max"] if job else salary + 15000,
            "RP %": round((salary / (job["Mid"] if job else salary)) * 100, 1)
        }
        employees.append(emp)
        current_id += 1
    
    return employees


# ─── Generate Reporting Structure ────────────────────────

def generate_reporting_structure(employees):
    """Build the org hierarchy by crawling each employee's manager chain."""
    emp_by_id = {e["Employee #"]: e for e in employees}
    
    rows = []
    # Get one row per employee (skip CEO since they report to no one)
    for emp in employees:
        if emp["Job Title"] == "CEO":
            continue
        
        emp_id = emp["Employee #"]
        name = emp["First Name Last Name"]
        
        # Crawl up the reporting chain
        current = emp
        reports_to = {}
        levels = []
        
        for level_idx in range(1, 8):  # Up to 7 levels
            manager_id = current.get("Reporting to", "")
            if not manager_id or manager_id == emp_id:
                break
            
            reports_to[f"Reports to {level_idx}"] = manager_id
            levels.append(f"Level {level_idx}")
            
            if manager_id in emp_by_id:
                current = emp_by_id[manager_id]
            else:
                break
        
        # Fill remaining levels with empty
        for level_idx in range(1, 8):
            key = f"Reports to {level_idx}"
            if key not in reports_to:
                reports_to[key] = ""
        
        # Identify exec chain
        director = ""
        e1 = ""
        first_exec = ""
        executive = ""
        skip_level = ""
        
        # Walk the chain again for role detection
        current = emp
        for level_idx in range(1, 8):
            manager_id = current.get("Reporting to", "")
            if not manager_id or manager_id == emp_id:
                break
            if manager_id in emp_by_id:
                mgr = emp_by_id[manager_id]
                level_val = mgr.get("Radford Level", "")
                if level_val and level_val[0] == "M" and int(level_val[1]) >= 3 and not director:
                    director = manager_id
                if level_val and level_val[0] == "E" and not first_exec:
                    first_exec = manager_id
                if level_val == "E1" and not e1:
                    e1 = manager_id
                if level_val in ("E5", "E6") and not executive:
                    executive = manager_id
                current = mgr
        
        row = {
            "Employee #": emp_id,
            "Name": name,
            "Reports to 1": reports_to.get("Reports to 1", ""),
            "Reports to 2": reports_to.get("Reports to 2", ""),
            "Reports to 3": reports_to.get("Reports to 3", ""),
            "Reports to 4": reports_to.get("Reports to 4", ""),
            "Reports to 5": reports_to.get("Reports to 5", ""),
            "Reports to 6": reports_to.get("Reports to 6", ""),
            "Reports to 7": reports_to.get("Reports to 7", ""),
            "Reports to 1 Level": levels[0] if len(levels) > 0 else "",
            "Reports to 2 Level": levels[1] if len(levels) > 1 else "",
            "Reports to 3 Level": levels[2] if len(levels) > 2 else "",
            "Reports to 4 Level": levels[3] if len(levels) > 3 else "",
            "Reports to 5 Level": levels[4] if len(levels) > 4 else "",
            "Reports to 6 Level": levels[5] if len(levels) > 5 else "",
            "Reports to 7 Level": levels[6] if len(levels) > 6 else "",
            "Director": director,
            "E-1": e1,
            "First Executive": first_exec,
            "Executive": executive,
            "Skip Level Manager": skip_level,
            "Employee Status": emp.get("Employment Status", "Active")
        }
        rows.append(row)
    
    return rows


# ─── Generate Current Team (Active Employees Only + Enrichments) ──

def generate_current_team(employees):
    active = [e for e in employees if e["Employment Status"] == "Active"]
    return active  # Same structure with enriched fields already populated


# ─── Write CSVs ──────────────────────────────────────────

def write_csv(path, data, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return len(data)

def main():
    output_dir = Path(__file__).parent / "people_chat" / "data" / "sample"
    
    print("Generating job catalog...")
    job_catalog = generate_job_catalog()
    
    print("Generating employees...")
    employees = generate_employees(job_catalog, num_employees=750)
    
    print("Generating reporting structure...")
    reporting = generate_reporting_structure(employees)
    
    print("Filtering current team...")
    current_team = [e for e in employees if e["Employment Status"] == "Active"]
    
    # Field lists
    data_dump_fields = [
        "Employee #", "First Name", "Preferred Name", "Last Name", "First Name Last Name",
        "Job Title", "Department", "Division", "Reporting to", "Hire Date",
        "Work Email", "Birth Date", "Gender", "Employment Status",
        "City", "State", "Zip Code", "Compensation: Date", "Pay rate",
        "Time Type", "Exempt", "Pay Schedule", "Termination Date",
        "Radford Level", "Bonus Type", "Bonus Amount", "EEID"
    ]
    
    current_team_fields = data_dump_fields + [
        "People Leader?", "Annualized Pay", "Annual Pay",
        "Director", "E-1", "First Executive", "Top Executive", "Skip Level Manager",
        "HRBP", "July Threshold", "Jan Threshold",
        "Job Code", "Band Number", "Min", "25% RP", "Mid", "75% RP", "Max", "RP %"
    ]
    
    reporting_fields = [
        "Employee #", "Name",
        "Reports to 1", "Reports to 2", "Reports to 3", "Reports to 4",
        "Reports to 5", "Reports to 6", "Reports to 7",
        "Reports to 1 Level", "Reports to 2 Level", "Reports to 3 Level",
        "Reports to 4 Level", "Reports to 5 Level", "Reports to 6 Level",
        "Reports to 7 Level",
        "Director", "E-1", "First Executive", "Executive", "Skip Level Manager",
        "Employee Status"
    ]
    
    job_catalog_fields = [
        "Job Code", "Position Title", "Department", "Division", "Job Family",
        "Active or Inactive", "Radford Level",
        "Benchmarking Code One", "Benchmarking One Percentage",
        "Benchmarking Code Two", "Benchmarking Two Percentage",
        "Band Number", "Range Min", "Quartile One Top", "Mid",
        "Quartile Three Top", "Max", "Set Rate",
        "AIP or Commissions", "AIP Percentage", "Commissions",
        "Hourly or Salary", "Exemption Status", "EEOC Category",
        "Job Description Link", "Equity Structure"
    ]
    
    # Write CSV files
    print(f"\nWriting {len(employees)} employees to employees.csv...")
    # Trim to data_dump_fields only
    employees_trimmed = [{k: e[k] for k in data_dump_fields} for e in employees]
    emp_count = write_csv(output_dir / "employees.csv", employees_trimmed, data_dump_fields)
    
    print(f"Writing {len(current_team)} active employees to current_team.csv...")
    active_trimmed = [{k: e[k] for k in current_team_fields if k in e} for e in current_team]
    ct_count = write_csv(output_dir / "current_team.csv", active_trimmed, current_team_fields)
    
    print(f"Writing {len(reporting)} org hierarchy rows to reporting_structure.csv...")
    rs_count = write_csv(output_dir / "reporting_structure.csv", reporting, reporting_fields)
    
    print(f"Writing {len(job_catalog)} job catalog entries to job_catalog.csv...")
    jc_count = write_csv(output_dir / "job_catalog.csv", job_catalog, job_catalog_fields)
    
    # Report
    print(f"\n{'='*50}")
    print(f"✅ Synthetic HR Data Generated")
    print(f"{'='*50}")
    print(f"  Company: {COMPANY_NAME}")
    print(f"  Employees:     {emp_count} rows  ({output_dir / 'employees.csv'})")
    print(f"  Current Team:  {ct_count} rows  ({output_dir / 'current_team.csv'})")
    print(f"  Org Hierarchy: {rs_count} rows  ({output_dir / 'reporting_structure.csv'})")
    print(f"  Job Catalog:   {jc_count} rows  ({output_dir / 'job_catalog.csv'})")
    
    # File sizes
    for fname in ["employees.csv", "current_team.csv", "reporting_structure.csv", "job_catalog.csv"]:
        fpath = output_dir / fname
        print(f"  {fname}: {fpath.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
