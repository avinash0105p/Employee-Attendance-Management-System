# Employee Attendance Management System

## Technologies
- Python
- FastAPI
- MySQL
- SQLAlchemy
- Pydantic

## Features

### Phase 1
- Employee CRUD APIs
- Attendance CRUD APIs
- Leave CRUD APIs

### Phase 2
- Roles: Admin, Manager, Employee
- Shared Users table
- Employee registration
- Admin creates Manager
- Password hashing (PBKDF2 SHA-256)
- Manager leave approval workflow
- Employee leave history
- Leave review timestamps

## Setup Steps

1. Install requirements:
   pip install -r requirements.txt

2. Run `migrate_phase2.sql` in MySQL to update tables without losing Phase 1 data.

3. Create the initial Admin account:
   python seed_admin.py

4. Start the FastAPI server:
   uvicorn main:app --reload

5. Open Swagger docs:
   http://127.0.0.1:8000/docs