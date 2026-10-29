# Phase 3 – Employee Attendance Management System

## Project Overview

Phase 3 enhances the Employee Attendance Management System developed in Phase 1 and Phase 2 using Python, FastAPI, MySQL, SQLAlchemy, HTML, CSS, and JavaScript.

This phase introduces JWT authentication, refresh tokens, role-based access control, and frontend dashboards for Admin, Manager, and Employee users.

## Technologies Used

- Python
- FastAPI
- MySQL
- SQLAlchemy
- JWT Authentication
- PyJWT
- HTML
- CSS
- JavaScript

## Features

### Authentication
- Login using email and password
- JWT access token generation
- Refresh token functionality
- Logout and session revocation
- Get current logged-in user details
- Validate authentication tokens

### Admin
- View Admin accounts
- Create and view Managers
- Register and manage Employees
- Manage attendance records
- View and manage leave requests

### Manager
- View assigned Employees
- View pending leave requests
- Approve or reject leave requests

### Employee
- View personal profile
- View attendance records
- Apply for leave
- View leave request status

### Frontend
- Login page
- Admin dashboard
- Manager dashboard
- Employee dashboard
- API integration using JavaScript Fetch
- Logout functionality

## Project Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root and configure the MySQL connection and JWT settings.

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/employee_attendance_db
JWT_SECRET_KEY=REPLACE_WITH_A_RANDOM_SECRET_AT_LEAST_32_CHARACTERS
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Replace the placeholders with your local configuration. Do not upload the actual `.env` file or secrets to GitHub.

### 3. Database Setup

- Create the `employee_attendance_db` database in MySQL.
- Apply the Phase 2 migration if it has not already been applied.
- Execute `migrate_phase3.sql` to create the Phase 3 token session table.

### 4. Initialize Admin

If an Admin account does not already exist, run:

```bash
python seed_admin.py
```

### 5. Run the Application

```bash
uvicorn main:app --reload
```

## Application URLs

- Frontend: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs

## Authentication Workflow

1. Log in using registered credentials.
2. Receive an access token and refresh token.
3. Use the access token to access protected APIs.
4. Use the refresh token to obtain a new token pair.
5. Log out to revoke the active session.

## Security

- Passwords are stored as hashes.
- Protected APIs require authentication and appropriate roles.
- Keep database credentials, JWT secrets, and tokens private.
- Do not commit `.env` or virtual environment folders.

## Project Status

Phase 3 builds on the existing Employee Attendance Management System by adding authentication, authorization, token refresh, and frontend integration.
