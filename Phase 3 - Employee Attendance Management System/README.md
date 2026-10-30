# Employee Attendance Management System - Phase 3

## Technologies

- Python
- FastAPI
- MySQL
- SQLAlchemy
- JWT Authentication
- HTML, CSS, JavaScript

## Features

### Authentication
- Login
- Logout
- JWT access token
- Refresh token
- Current user details
- Token revocation

### Admin
- Create Manager
- Register Employee
- View and manage Employees
- Manage Attendance
- View Leave Requests

### Manager
- View assigned Employees
- View pending Leave Requests
- Approve or Reject Leaves

### Employee
- View Profile
- View Attendance
- Apply for Leave
- View Leave Status

## Setup

1. Install Python and MySQL.
2. Open the existing project folder.
3. Install dependencies:

   pip install -r requirements.txt

4. Configure database and JWT secrets in `.env`.
5. Run `migrate_phase3.sql` in MySQL Workbench.
6. Make sure Phase 2 roles and tables exist.
7. If an Admin account does not exist, run:

   python seed_admin.py

8. Start the server from the project root:

   uvicorn main:app --reload

9. Open Swagger:

   http://127.0.0.1:8000/docs

10. Open the frontend:

    http://127.0.0.1:8000/

## Testing

1. Login using the Admin account.
2. Copy the access token from the login response.
3. Click Authorize in Swagger and enter:

   Bearer YOUR_ACCESS_TOKEN

4. Test protected endpoints.
5. Test refresh using `/auth/refresh`.
6. Test logout using `/auth/logout`.
7. Verify that the old access token fails after logout.
8. Verify that Manager and Employee accounts cannot access
   unauthorized records.
