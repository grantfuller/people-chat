-- Question: "How many active employees do we have?"
-- SQL:
SELECT COUNT(*) AS headcount
FROM employees
WHERE "Employment Status" = 'Active'

-- Question: "What's the average salary by department?"
-- SQL:
SELECT "Department",
       ROUND(AVG("Pay rate"), 0) AS avg_salary,
       COUNT(*) AS employee_count
FROM employees
WHERE "Employment Status" = 'Active'
GROUP BY "Department"
ORDER BY avg_salary DESC

-- Question: "Which department has the highest turnover?"
-- SQL:
-- Turnover = voluntary exits / avg headcount (approximation)
SELECT "Department",
       SUM(CASE WHEN "Termination Date" IS NOT NULL THEN 1 ELSE 0 END) AS exits,
       COUNT(*) AS total_employees,
       ROUND(CAST(SUM(CASE WHEN "Termination Date" IS NOT NULL THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100, 1) AS turnover_pct
FROM employees
GROUP BY "Department"
ORDER BY turnover_pct DESC

-- Question: "Show me the top 10 highest paid employees"
-- SQL:
SELECT "First Name Last Name" AS employee_name,
       "Job Title",
       "Department",
       "Pay rate" AS salary
FROM employees
WHERE "Employment Status" = 'Active'
ORDER BY "Pay rate" DESC
LIMIT 10

-- Question: "What's the average tenure in years by department?"
-- SQL:
SELECT "Department",
       ROUND(AVG(JULIANDAY(COALESCE("Termination Date", DATE('now'))) - JULIANDAY("Hire Date")) / 365.25, 1) AS avg_tenure_years
FROM employees
GROUP BY "Department"
ORDER BY avg_tenure_years DESC

-- Question: "How many employees are in each employment status?"
-- SQL:
SELECT "Employment Status",
       COUNT(*) AS count
FROM employees
GROUP BY "Employment Status"
ORDER BY count DESC

-- Question: "Show me the gender distribution by department"
-- SQL:
SELECT "Department",
       "Gender",
       COUNT(*) AS count
FROM employees
WHERE "Gender" IS NOT NULL AND "Gender" <> ''
GROUP BY "Department", "Gender"
ORDER BY "Department", count DESC

-- Question: "What's the salary range (min, max, avg) for each Radford level?"
-- SQL:
SELECT "Radford Level",
       MIN("Pay rate") AS min_salary,
       MAX("Pay rate") AS max_salary,
       ROUND(AVG("Pay rate"), 0) AS avg_salary,
       COUNT(*) AS employee_count
FROM employees
WHERE "Employment Status" = 'Active' AND "Radford Level" IS NOT NULL
GROUP BY "Radford Level"
ORDER BY "Radford Level"

-- Question: "Show me employees with above-average salary in their department"
-- SQL:
SELECT e."First Name Last Name",
       e."Job Title",
       e."Department",
       e."Pay rate" AS salary,
       ROUND(dept.avg_dept_salary, 0) AS dept_avg,
       ROUND((e."Pay rate" - dept.avg_dept_salary) / dept.avg_dept_salary * 100, 1) AS pct_above_avg
FROM employees e
JOIN (
    SELECT "Department", AVG("Pay rate") AS avg_dept_salary
    FROM employees
    WHERE "Employment Status" = 'Active'
    GROUP BY "Department"
) dept ON e."Department" = dept."Department"
WHERE e."Employment Status" = 'Active'
  AND e."Pay rate" > dept.avg_dept_salary
ORDER BY pct_above_avg DESC

-- Question: "Show me headcount trend by year"
-- SQL:
SELECT STRFTIME('%Y', "Hire Date") AS hire_year,
       COUNT(*) AS hires
FROM employees
GROUP BY hire_year
ORDER BY hire_year

-- Question: "How many people report to each manager?"
-- SQL:
SELECT "Reporting to" AS manager_id,
       COUNT(*) AS direct_reports
FROM employees
WHERE "Employment Status" = 'Active'
  AND "Reporting to" IS NOT NULL
  AND "Reporting to" <> ''
GROUP BY "Reporting to"
ORDER BY direct_reports DESC

-- Question: "What is the compa-ratio distribution? (salary vs band midpoint)"
-- SQL:
SELECT
    CASE
        WHEN "Pay rate" * 1.0 / "Mid" < 0.8 THEN 'Below Range (<80%)'
        WHEN "Pay rate" * 1.0 / "Mid" < 1.0 THEN 'Lower Half (80-100%)'
        WHEN "Pay rate" * 1.0 / "Mid" < 1.2 THEN 'Upper Half (100-120%)'
        ELSE 'Above Range (>120%)'
    END AS compa_ratio_band,
    COUNT(*) AS employee_count,
    ROUND(AVG(("Pay rate" * 1.0 / "Mid") * 100), 1) AS avg_rp_pct
FROM employees
WHERE "Employment Status" = 'Active'
  AND "Mid" IS NOT NULL AND "Mid" > 0
GROUP BY compa_ratio_band
ORDER BY avg_rp_pct
