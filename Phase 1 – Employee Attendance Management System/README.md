
# NOTE : THIS README WAS WRITTEN USING AI

# Employee Attendance Management System

## Phase 1

This project is a basic Employee Attendance Management System developed using:

- Python
- FastAPI
- MySQL
- SQLAlchemy
- Pydantic

## Features

### Employee Management

- Add Employee
- Get All Employees
- Get Employee by ID
- Update Employee
- Delete Employee

### Attendance Management

- Mark Attendance
- Get All Attendance
- Get Attendance by Employee ID
- Update Attendance
- Delete Attendance

### Leave Management

- Apply Leave
- Get All Leave Requests
- Get Leave by ID
- Update Leave
- Delete Leave

## Project Structure

employee_attendance_system/

    main.py
    database.py
    models.py
    schemas.py
    sample_data.sql
    requirements.txt
    README.md

## Database Setup

1. Open MySQL.
2. Run the `sample_data.sql` file.
3. Make sure the database `employee_attendance_db` is created.
4. Update the MySQL password in `database.py`.

Example:

    DATABASE_URL = "mysql+mysqlconnector://root:your_password@localhost/employee_attendance_db"

## Install Requirements

Run:

    pip install -r requirements.txt

## Run the Application

Run:

    uvicorn main:app --reload

## Swagger Documentation

Open the browser and go to:

    http://127.0.0.1:8000/docs

Swagger can be used to test all APIs.

## Attendance Status

Allowed values:

- Present
- Absent
- Leave

## Leave Status

Allowed values:

- Pending
- Approved
- Rejected

## Phase 1 Scope

Phase 1 contains basic CRUD operations.

The approval workflow will be implemented in the next phase.
