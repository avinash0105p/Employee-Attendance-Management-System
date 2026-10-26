from datetime import datetime
import hashlib
import secrets

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_database
from models import Role, User, Employee, Attendance, LeaveRequest
from schemas import (
    RegisterEmployee, CreateManager, UserResponse,
    CreateEmployee, UpdateEmployee, EmployeeResponse,
    CreateAttendance, UpdateAttendance, AttendanceResponse,
    CreateLeave, UpdateLeave, LeaveResponse, LeaveReview
)

Base.metadata.create_all(bind=engine)

# Swagger parameters set chesam - docExpansion none ante default ga anni topics close ayyi headings la kanipisthayi
app = FastAPI(
    title="Employee Attendance Management System - Phase 2",
    swagger_ui_parameters={"docExpansion": "none"}
)

# Password Hashing Helper
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600000
    ).hex()
    return f"{salt}${password_hash}"

# Helper Queries
def get_role(db: Session, role_name: str):
    return db.query(Role).filter(Role.role_name == role_name).first()

def get_user_by_role(db: Session, user_id: int, role_name: str):
    user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
    if user is None:
        return None
    role = db.query(Role).filter(Role.role_id == user.role_id, Role.role_name == role_name).first()
    if role is None:
        return None
    return user

def fetch_employee(db: Session, employee_id: int):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

def fetch_leave(db: Session, leave_id: int):
    leave = db.query(LeaveRequest).filter(LeaveRequest.leave_id == leave_id).first()
    if leave is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave


# ==========================================
# 1. ADMIN MANAGEMENT
# ==========================================

@app.post("/admin/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["1. Admin Management"])
def create_admin(full_name: str, email: str, phone: str, password: str, db: Session = Depends(get_database)):
    admin_role = get_role(db, "Admin")
    if not admin_role:
        raise HTTPException(status_code=500, detail="Admin role not found")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_admin = User(
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role_id=admin_role.role_id,
        is_active=True
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin


@app.get("/admin", response_model=list[UserResponse], tags=["1. Admin Management"])
def get_admin_details(db: Session = Depends(get_database)):
    admin_role = get_role(db, "Admin")
    if not admin_role:
        raise HTTPException(status_code=404, detail="Admin role not found")

    admins = db.query(User).filter(
        User.role_id == admin_role.role_id,
        User.is_active == True
    ).all()
    return admins


@app.post("/admin/managers", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["1. Admin Management"])
def create_manager(manager_data: CreateManager, db: Session = Depends(get_database)):
    admin = get_user_by_role(db, manager_data.admin_id, "Admin")
    if admin is None:
        raise HTTPException(status_code=403, detail="Invalid or inactive Admin ID")

    if db.query(User).filter(User.email == manager_data.email).first():
        raise HTTPException(status_code=400, detail="Email address already exists")

    manager_role = get_role(db, "Manager")
    if manager_role is None:
        raise HTTPException(status_code=500, detail="Manager role is missing. Run database migration.")

    try:
        new_manager = User(
            full_name=manager_data.full_name,
            email=manager_data.email,
            phone=manager_data.phone,
            password_hash=hash_password(manager_data.password),
            role_id=manager_role.role_id,
            is_active=True
        )
        db.add(new_manager)
        db.commit()
        db.refresh(new_manager)
        return new_manager
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or phone number already exists")


@app.get("/admin/managers", response_model=list[UserResponse], tags=["1. Admin Management"])
def get_all_managers(db: Session = Depends(get_database)):
    manager_role = get_role(db, "Manager")
    if not manager_role:
        raise HTTPException(status_code=404, detail="Manager role not found")

    managers = db.query(User).filter(
        User.role_id == manager_role.role_id,
        User.is_active == True
    ).all()
    return managers


# ==========================================
# 2. AUTHENTICATION & REGISTRATION
# ==========================================
@app.post("/auth/register-employee", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["2. Authentication"])
def register_employee(employee_data: RegisterEmployee, db: Session = Depends(get_database)):
    manager = get_user_by_role(db, employee_data.manager_id, "Manager")
    if manager is None:
        raise HTTPException(status_code=400, detail="Invalid or inactive Manager ID")

    if db.query(User).filter(User.email == employee_data.email).first():
        raise HTTPException(status_code=400, detail="Email address already exists")

    employee_role = get_role(db, "Employee")
    if employee_role is None:
        raise HTTPException(status_code=500, detail="Employee role is missing. Run database migration.")

    try:
        new_user = User(
            full_name=employee_data.full_name,
            email=employee_data.email,
            phone=employee_data.phone,
            password_hash=hash_password(employee_data.password),
            role_id=employee_role.role_id,
            is_active=True
        )
        db.add(new_user)
        db.flush()

        new_employee = Employee(
            employee_name=employee_data.full_name,
            email=employee_data.email,
            phone=employee_data.phone,
            department=employee_data.department,
            designation=employee_data.designation,
            user_id=new_user.user_id,
            manager_id=manager.user_id
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or phone number already exists")


# ==========================================
# 3. MANAGER LEAVE APPROVAL WORKFLOW
# ==========================================
@app.get("/manager/{manager_id}/leaves/pending", response_model=list[LeaveResponse], tags=["3. Manager Leave Approval"])
def get_manager_pending_leaves(manager_id: int, db: Session = Depends(get_database)):
    manager = get_user_by_role(db, manager_id, "Manager")
    if manager is None:
        raise HTTPException(status_code=403, detail="Invalid or inactive Manager ID")

    assigned_employees = db.query(Employee.employee_id).filter(Employee.manager_id == manager_id).subquery()
    return db.query(LeaveRequest).filter(
        LeaveRequest.employee_id.in_(assigned_employees),
        LeaveRequest.status == "Pending"
    ).order_by(LeaveRequest.leave_id).all()


@app.post("/manager/leaves/{leave_id}/review", response_model=LeaveResponse, tags=["3. Manager Leave Approval"])
def review_leave(leave_id: int, review: LeaveReview, db: Session = Depends(get_database)):
    manager = get_user_by_role(db, review.manager_id, "Manager")
    if manager is None:
        raise HTTPException(status_code=403, detail="Invalid or inactive Manager ID")

    leave = fetch_leave(db, leave_id)
    if leave.status != "Pending":
        raise HTTPException(status_code=400, detail="Leave request has already been processed")

    employee = fetch_employee(db, leave.employee_id)
    if employee.manager_id != manager.user_id:
        raise HTTPException(status_code=403, detail="Only the assigned Manager can review this leave")

    leave.status = review.action
    leave.reviewed_by = manager.user_id
    leave.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(leave)
    return leave


# ==========================================
# 4. EMPLOYEE MANAGEMENT
# ==========================================
@app.get("/employees", response_model=list[EmployeeResponse], tags=["4. Employee Management"])
def get_all_employees(db: Session = Depends(get_database)):
    return db.query(Employee).all()


@app.post("/employees", response_model=EmployeeResponse, tags=["4. Employee Management"])
def add_employee(employee: CreateEmployee, db: Session = Depends(get_database)):
    if db.query(Employee).filter((Employee.email == employee.email) | (Employee.phone == employee.phone)).first():
        raise HTTPException(status_code=400, detail="Email or phone number already exists")

    new_employee = Employee(
        employee_name=employee.employee_name,
        email=employee.email,
        phone=employee.phone,
        department=employee.department,
        designation=employee.designation
    )
    try:
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        return new_employee
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or phone number already exists")


@app.get("/employees/{employee_id}", response_model=EmployeeResponse, tags=["4. Employee Management"])
def get_employee_by_id(employee_id: int, db: Session = Depends(get_database)):
    return fetch_employee(db, employee_id)


@app.put("/employees/{employee_id}", response_model=EmployeeResponse, tags=["4. Employee Management"])
def update_employee(employee_id: int, employee: UpdateEmployee, db: Session = Depends(get_database)):
    existing = fetch_employee(db, employee_id)

    duplicate = db.query(Employee).filter(
        Employee.employee_id != employee_id,
        ((Employee.email == employee.email) | (Employee.phone == employee.phone))
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Email or phone number already exists")

    existing.employee_name = employee.employee_name
    existing.email = employee.email
    existing.phone = employee.phone
    existing.department = employee.department
    existing.designation = employee.designation

    if existing.user_id is not None:
        linked_user = db.query(User).filter(User.user_id == existing.user_id).first()
        if linked_user:
            linked_user.full_name = employee.employee_name
            linked_user.email = employee.email
            linked_user.phone = employee.phone

    try:
        db.commit()
        db.refresh(existing)
        return existing
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or phone number already exists")


@app.delete("/employees/{employee_id}", tags=["4. Employee Management"])
def delete_employee(employee_id: int, db: Session = Depends(get_database)):
    employee = fetch_employee(db, employee_id)
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}


# ==========================================
# 5. ATTENDANCE MANAGEMENT
# ==========================================
@app.get("/attendance", response_model=list[AttendanceResponse], tags=["5. Attendance Management"])
def get_all_attendance(db: Session = Depends(get_database)):
    return db.query(Attendance).all()


@app.post("/attendance", response_model=AttendanceResponse, tags=["5. Attendance Management"])
def mark_attendance(attendance: CreateAttendance, db: Session = Depends(get_database)):
    fetch_employee(db, attendance.employee_id)
    new_attendance = Attendance(
        employee_id=attendance.employee_id,
        attendance_date=attendance.attendance_date,
        status=attendance.status
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return new_attendance


@app.get("/attendance/employee/{employee_id}", response_model=list[AttendanceResponse], tags=["5. Attendance Management"])
def get_attendance_by_employee(employee_id: int, db: Session = Depends(get_database)):
    fetch_employee(db, employee_id)
    return db.query(Attendance).filter(Attendance.employee_id == employee_id).all()


@app.put("/attendance/{attendance_id}", response_model=AttendanceResponse, tags=["5. Attendance Management"])
def update_attendance(attendance_id: int, attendance: UpdateAttendance, db: Session = Depends(get_database)):
    existing = db.query(Attendance).filter(Attendance.attendance_id == attendance_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    fetch_employee(db, attendance.employee_id)
    existing.employee_id = attendance.employee_id
    existing.attendance_date = attendance.attendance_date
    existing.status = attendance.status

    db.commit()
    db.refresh(existing)
    return existing


@app.delete("/attendance/{attendance_id}", tags=["5. Attendance Management"])
def delete_attendance(attendance_id: int, db: Session = Depends(get_database)):
    existing = db.query(Attendance).filter(Attendance.attendance_id == attendance_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(existing)
    db.commit()
    return {"message": "Attendance deleted successfully"}


# ==========================================
# 6. LEAVE MANAGEMENT
# ==========================================
@app.get("/leaves", response_model=list[LeaveResponse], tags=["6. Leave Management"])
def get_all_leaves(db: Session = Depends(get_database)):
    return db.query(LeaveRequest).all()


@app.post("/leaves", response_model=LeaveResponse, tags=["6. Leave Management"])
def apply_leave(leave: CreateLeave, db: Session = Depends(get_database)):
    fetch_employee(db, leave.employee_id)
    if leave.from_date > leave.to_date:
        raise HTTPException(status_code=400, detail="From date cannot be greater than To date")

    new_leave = LeaveRequest(
        employee_id=leave.employee_id,
        from_date=leave.from_date,
        to_date=leave.to_date,
        leave_type=leave.leave_type,
        reason=leave.reason,
        status="Pending"
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave


@app.get("/leaves/{leave_id}", response_model=LeaveResponse, tags=["6. Leave Management"])
def get_leave_by_id(leave_id: int, db: Session = Depends(get_database)):
    return fetch_leave(db, leave_id)


@app.put("/leaves/{leave_id}", response_model=LeaveResponse, tags=["6. Leave Management"])
def update_leave(leave_id: int, leave: UpdateLeave, db: Session = Depends(get_database)):
    existing = fetch_leave(db, leave_id)
    if existing.status != "Pending":
        raise HTTPException(status_code=400, detail="Already processed leave cannot be updated")

    if leave.from_date > leave.to_date:
        raise HTTPException(status_code=400, detail="From date cannot be greater than To date")

    existing.from_date = leave.from_date
    existing.to_date = leave.to_date
    existing.leave_type = leave.leave_type
    existing.reason = leave.reason

    db.commit()
    db.refresh(existing)
    return existing


@app.delete("/leaves/{leave_id}", tags=["6. Leave Management"])
def delete_leave(leave_id: int, db: Session = Depends(get_database)):
    existing = fetch_leave(db, leave_id)
    if existing.status != "Pending":
        raise HTTPException(status_code=400, detail="Already processed leave cannot be deleted")

    db.delete(existing)
    db.commit()
    return {"message": "Leave request deleted successfully"}


@app.get("/employees/{employee_id}/leaves", response_model=list[LeaveResponse], tags=["6. Leave Management"])
def get_employee_leave_history(employee_id: int, db: Session = Depends(get_database)):
    fetch_employee(db, employee_id)
    return db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id
    ).order_by(LeaveRequest.leave_id.desc()).all()