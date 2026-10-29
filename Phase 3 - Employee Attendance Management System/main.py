import hashlib
import secrets
import uuid

from datetime import datetime, timedelta, timezone

import jwt

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_database
from models import (
    User, Role, Employee, Attendance, LeaveRequest, TokenSession
)
from schemas import (
    LoginRequest, RefreshRequest, TokenResponse,
    UserResponse, CreateManager, RegisterEmployee,
    CreateEmployee, UpdateEmployee, EmployeeResponse,
    CreateAttendance, UpdateAttendance, AttendanceResponse,
    CreateLeave, UpdateLeave, LeaveResponse, LeaveReview
)
from auth import (
    JWT_SECRET_KEY, JWT_ALGORITHM,
    ACCESS_TOKEN_MINUTES, REFRESH_TOKEN_DAYS,
    create_token, get_current_user, require_roles,
    verify_password, hash_password
)


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Employee Attendance Management System - Phase 3",
    swagger_ui_parameters={"docExpansion": "none"}
)


def get_role(db: Session, role_name: str):
    return db.query(Role).filter(
        Role.role_name == role_name
    ).first()


def get_employee_for_user(db: Session, user_id: int):
    employee = db.query(Employee).filter(
        Employee.user_id == user_id
    ).first()

    if employee is None:
        raise HTTPException(404, "Employee record not found")

    return employee


def get_employee_or_404(db: Session, employee_id: int):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if employee is None:
        raise HTTPException(404, "Employee not found")

    return employee


def check_employee_access(db, user, employee):
    if user.role_name == "Admin":
        return

    if user.role_name == "Manager" and employee.manager_id == user.user_id:
        return

    if user.role_name == "Employee" and employee.user_id == user.user_id:
        return

    raise HTTPException(403, "You cannot access this employee's records")


def check_manager_access(user, employee):
    if user.role_name == "Admin":
        return

    if (
        user.role_name == "Manager"
        and employee.manager_id == user.user_id
    ):
        return

    raise HTTPException(403, "Only the assigned Manager can access this record")


def get_leave_or_404(db, leave_id: int):
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.leave_id == leave_id
    ).first()

    if leave is None:
        raise HTTPException(404, "Leave request not found")

    return leave


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

@app.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(data: LoginRequest, db: Session = Depends(get_database)):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if (
        user is None
        or not user.is_active
        or user.password_hash == "RESET_REQUIRED"
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(401, "Invalid email or password")

    role = db.query(Role).filter(
        Role.role_id == user.role_id
    ).first()

    if role is None:
        raise HTTPException(500, "User role is not configured")

    session_id = str(uuid.uuid4())

    refresh_token, refresh_payload = create_token(
        user.user_id,
        session_id,
        "refresh",
        timedelta(days=REFRESH_TOKEN_DAYS)
    )

    session = TokenSession(
        session_id=session_id,
        user_id=user.user_id,
        refresh_jti=refresh_payload["jti"],
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(days=REFRESH_TOKEN_DAYS)
        ).replace(tzinfo=None),
        revoked=False
    )

    db.add(session)
    db.commit()

    access_token, _ = create_token(
        user.user_id,
        session_id,
        "access",
        timedelta(minutes=ACCESS_TOKEN_MINUTES)
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=role.role_name,
        user_id=user.user_id,
        full_name=user.full_name
    )


@app.post("/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_database)
):
    unauthorized = HTTPException(
        401,
        "Invalid, expired, or revoked refresh token"
    )

    try:
        payload = jwt.decode(
            data.refresh_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise unauthorized

        user_id = int(payload["sub"])
        session_id = payload["sid"]
        old_jti = payload["jti"]

    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise unauthorized

    session = db.query(TokenSession).filter(
        TokenSession.session_id == session_id,
        TokenSession.user_id == user_id,
        TokenSession.revoked.is_(False),
        TokenSession.refresh_jti == old_jti
    ).first()

    if (
        session is None
        or session.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None)
    ):
        raise unauthorized

    user = db.query(User).filter(
        User.user_id == user_id,
        User.is_active.is_(True)
    ).first()

    if user is None:
        raise unauthorized

    role = db.query(Role).filter(
        Role.role_id == user.role_id
    ).first()

    if role is None:
        raise unauthorized

    # Rotate refresh token: old refresh token cannot be reused.
    new_refresh, refresh_payload = create_token(
        user.user_id,
        session_id,
        "refresh",
        timedelta(days=REFRESH_TOKEN_DAYS)
    )

    session.refresh_jti = refresh_payload["jti"]
    session.expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=REFRESH_TOKEN_DAYS)
    ).replace(tzinfo=None)

    db.commit()

    new_access, _ = create_token(
        user.user_id,
        session_id,
        "access",
        timedelta(minutes=ACCESS_TOKEN_MINUTES)
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        role=role.role_name,
        user_id=user.user_id,
        full_name=user.full_name
    )


@app.post("/auth/logout", tags=["Authentication"])
def logout(
    user=Depends(get_current_user),
    db: Session = Depends(get_database)
):
    session = db.query(TokenSession).filter(
        TokenSession.session_id == user.session_id
    ).first()

    if session is None or session.revoked:
        raise HTTPException(401, "Session already logged out")

    session.revoked = True
    db.commit()

    return {"message": "Logout successful"}


@app.get("/auth/me", tags=["Authentication"])
def get_me(
    user=Depends(get_current_user),
    db: Session = Depends(get_database)
):
    return {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role_name,
        "is_active": user.is_active
    }


# --------------------------------------------------
# ADMIN APIs
# --------------------------------------------------

@app.get("/admin/admins", tags=["Admin"])
def get_admins(
    db: Session = Depends(get_database),
    current_user: User = Depends(require_roles("Admin"))
):
    admins = (
        db.query(User)
        .join(Role, User.role_id == Role.role_id)
        .filter(Role.role_name == "Admin")
        .all()
    )

    return [
        {
            "user_id": admin.user_id,
            "full_name": admin.full_name,
            "email": admin.email,
            "role": "Admin",
            "is_active": admin.is_active
        }
        for admin in admins
    ]

@app.post(
    "/admin/managers",
    response_model=UserResponse,
    status_code=201,
    tags=["Admin"]
)
def create_manager(
    data: CreateManager,
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    if db.query(User).filter(
        (User.email == data.email) | (User.phone == data.phone)
    ).first():
        raise HTTPException(400, "Email or phone already exists")

    role = get_role(db, "Manager")

    if role is None:
        raise HTTPException(500, "Manager role is missing")

    manager = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role_id=role.role_id,
        is_active=True
    )

    try:
        db.add(manager)
        db.commit()
        db.refresh(manager)
        return manager
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Email or phone already exists")


@app.get(
    "/admin/managers",
    response_model=list[UserResponse],
    tags=["Admin"]
)
def get_managers(
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    role = get_role(db, "Manager")

    return db.query(User).filter(
        User.role_id == role.role_id,
        User.is_active.is_(True)
    ).all()


@app.post(
    "/auth/register-employee",
    response_model=UserResponse,
    status_code=201,
    tags=["Admin"]
)
def register_employee(
    data: RegisterEmployee,
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    manager = db.query(User).join(
        Role, Role.role_id == User.role_id
    ).filter(
        User.user_id == data.manager_id,
        User.is_active.is_(True),
        Role.role_name == "Manager"
    ).first()

    if manager is None:
        raise HTTPException(400, "Invalid Manager ID")

    if db.query(User).filter(
        (User.email == data.email) | (User.phone == data.phone)
    ).first():
        raise HTTPException(400, "Email or phone already exists")

    role = get_role(db, "Employee")

    if role is None:
        raise HTTPException(500, "Employee role is missing")

    try:
        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role_id=role.role_id,
            is_active=True
        )

        db.add(user)
        db.flush()

        employee = Employee(
            employee_name=data.full_name,
            email=data.email,
            phone=data.phone,
            department=data.department,
            designation=data.designation,
            user_id=user.user_id,
            manager_id=manager.user_id
        )

        db.add(employee)
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Email or phone already exists")


@app.get(
    "/employees",
    response_model=list[EmployeeResponse],
    tags=["Employees"]
)
def get_employees(
    db: Session = Depends(get_database),
    user=Depends(get_current_user)
):
    if user.role_name == "Admin":
        return db.query(Employee).all()

    if user.role_name == "Manager":
        return db.query(Employee).filter(
            Employee.manager_id == user.user_id
        ).all()

    raise HTTPException(403, "Only Admin or Manager can list employees")


@app.post(
    "/employees",
    response_model=EmployeeResponse,
    status_code=201,
    tags=["Employees"]
)
def add_employee(
    data: CreateEmployee,
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    if db.query(Employee).filter(
        (Employee.email == data.email) | (Employee.phone == data.phone)
    ).first():
        raise HTTPException(400, "Email or phone already exists")

    employee = Employee(**data.model_dump())

    try:
        db.add(employee)
        db.commit()
        db.refresh(employee)
        return employee
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Email or phone already exists")


@app.get(
    "/employees/me",
    tags=["Employee"]
)
def get_my_employee_profile(
    db: Session = Depends(get_database),
    user=Depends(require_roles("Employee"))
):
    employee = get_employee_for_user(db, user.user_id)
    return employee


@app.get(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    tags=["Employees"]
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_database),
    user=Depends(get_current_user)
):
    employee = get_employee_or_404(db, employee_id)
    check_employee_access(db, user, employee)
    return employee


@app.put(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    tags=["Employees"]
)
def update_employee(
    employee_id: int,
    data: UpdateEmployee,
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    employee = get_employee_or_404(db, employee_id)

    if db.query(Employee).filter(
        Employee.employee_id != employee_id,
        (
            (Employee.email == data.email)
            | (Employee.phone == data.phone)
        )
    ).first():
        raise HTTPException(400, "Email or phone already exists")

    for key, value in data.model_dump().items():
        setattr(employee, key, value)

    linked_user = db.query(User).filter(
        User.user_id == employee.user_id
    ).first()

    if linked_user:
        linked_user.full_name = data.employee_name
        linked_user.email = data.email
        linked_user.phone = data.phone

    try:
        db.commit()
        db.refresh(employee)
        return employee
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Email or phone already exists")


@app.delete("/employees/{employee_id}", tags=["Employees"])
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    employee = get_employee_or_404(db, employee_id)
    db.delete(employee)
    db.commit()

    return {"message": "Employee deleted successfully"}


# --------------------------------------------------
# ATTENDANCE
# --------------------------------------------------

@app.get("/attendance", response_model=list[AttendanceResponse], tags=["Attendance"])
def get_attendance(
    db: Session = Depends(get_database),
    user=Depends(require_roles("Admin"))
):
    return db.query(Attendance).all()


@app.post(
    "/attendance",
    response_model=AttendanceResponse,
    status_code=201,
    tags=["Attendance"]
)
def mark_attendance(
    data: CreateAttendance,
    db: Session = Depends(get_database),
    user=Depends(require_roles("Admin"))
):
    get_employee_or_404(db, data.employee_id)

    record = Attendance(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@app.get(
    "/attendance/me",
    response_model=list[AttendanceResponse],
    tags=["Employee"]
)
def get_my_attendance(
    db: Session = Depends(get_database),
    user=Depends(require_roles("Employee"))
):
    employee = get_employee_for_user(db, user.user_id)

    return db.query(Attendance).filter(
        Attendance.employee_id == employee.employee_id
    ).order_by(Attendance.attendance_date.desc()).all()


@app.get(
    "/attendance/employee/{employee_id}",
    response_model=list[AttendanceResponse],
    tags=["Attendance"]
)
def get_employee_attendance(
    employee_id: int,
    db: Session = Depends(get_database),
    user=Depends(get_current_user)
):
    employee = get_employee_or_404(db, employee_id)
    check_employee_access(db, user, employee)

    return db.query(Attendance).filter(
        Attendance.employee_id == employee_id
    ).all()


@app.put(
    "/attendance/{attendance_id}",
    response_model=AttendanceResponse,
    tags=["Attendance"]
)
def update_attendance(
    attendance_id: int,
    data: UpdateAttendance,
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    record = db.query(Attendance).filter(
        Attendance.attendance_id == attendance_id
    ).first()

    if record is None:
        raise HTTPException(404, "Attendance record not found")

    get_employee_or_404(db, data.employee_id)

    for key, value in data.model_dump().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@app.delete("/attendance/{attendance_id}", tags=["Attendance"])
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_database),
    admin=Depends(require_roles("Admin"))
):
    record = db.query(Attendance).filter(
        Attendance.attendance_id == attendance_id
    ).first()

    if record is None:
        raise HTTPException(404, "Attendance record not found")

    db.delete(record)
    db.commit()

    return {"message": "Attendance deleted successfully"}


# --------------------------------------------------
# LEAVE MANAGEMENT
# --------------------------------------------------

@app.post(
    "/leaves",
    response_model=LeaveResponse,
    status_code=201,
    tags=["Leave"]
)
def apply_leave(
    data: CreateLeave,
    db: Session = Depends(get_database),
    user=Depends(require_roles("Employee"))
):
    employee = get_employee_for_user(db, user.user_id)

    if data.from_date > data.to_date:
        raise HTTPException(400, "From date cannot be after To date")

    leave = LeaveRequest(
        employee_id=employee.employee_id,
        from_date=data.from_date,
        to_date=data.to_date,
        leave_type=data.leave_type,
        reason=data.reason,
        status="Pending"
    )

    db.add(leave)
    db.commit()
    db.refresh(leave)

    return leave


@app.get(
    "/leaves/me",
    response_model=list[LeaveResponse],
    tags=["Employee"]
)
def get_my_leaves(
    db: Session = Depends(get_database),
    user=Depends(require_roles("Employee"))
):
    employee = get_employee_for_user(db, user.user_id)

    return db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee.employee_id
    ).order_by(LeaveRequest.leave_id.desc()).all()


@app.get(
    "/leaves",
    response_model=list[LeaveResponse],
    tags=["Leave"]
)
def get_leaves(
    db: Session = Depends(get_database),
    user=Depends(require_roles("Admin"))
):
    return db.query(LeaveRequest).all()


@app.get(
    "/leaves/{leave_id}",
    response_model=LeaveResponse,
    tags=["Leave"]
)
def get_leave(
    leave_id: int,
    db: Session = Depends(get_database),
    user=Depends(get_current_user)
):
    leave = get_leave_or_404(db, leave_id)
    employee = get_employee_or_404(db, leave.employee_id)

    check_employee_access(db, user, employee)
    return leave


@app.put(
    "/leaves/{leave_id}",
    response_model=LeaveResponse,
    tags=["Leave"]
)
def update_leave(
    leave_id: int,
    data: UpdateLeave,
    db: Session = Depends(get_database),
    user=Depends(require_roles("Employee"))
):
    leave = get_leave_or_404(db, leave_id)
    employee = get_employee_for_user(db, user.user_id)

    if leave.employee_id != employee.employee_id:
        raise HTTPException(403, "You cannot update another employee's leave")

    if leave.status != "Pending":
        raise HTTPException(400, "Processed leave cannot be updated")

    if data.from_date > data.to_date:
        raise HTTPException(400, "From date cannot be after To date")

    for key, value in data.model_dump().items():
        setattr(leave, key, value)

    db.commit()
    db.refresh(leave)
    return leave


@app.delete("/leaves/{leave_id}", tags=["Leave"])
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_database),
    user=Depends(require_roles("Employee"))
):
    leave = get_leave_or_404(db, leave_id)
    employee = get_employee_for_user(db, user.user_id)

    if leave.employee_id != employee.employee_id:
        raise HTTPException(403, "You cannot delete another employee's leave")

    if leave.status != "Pending":
        raise HTTPException(400, "Processed leave cannot be deleted")

    db.delete(leave)
    db.commit()

    return {"message": "Leave request deleted successfully"}


@app.get(
    "/employees/{employee_id}/leaves",
    response_model=list[LeaveResponse],
    tags=["Leave"]
)
def get_employee_leave_history(
    employee_id: int,
    db: Session = Depends(get_database),
    user=Depends(get_current_user)
):
    employee = get_employee_or_404(db, employee_id)
    check_employee_access(db, user, employee)

    return db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id
    ).order_by(LeaveRequest.leave_id.desc()).all()


# --------------------------------------------------
# MANAGER LEAVE APPROVAL
# --------------------------------------------------

@app.get(
    "/manager/me/employees",
    response_model=list[EmployeeResponse],
    tags=["Manager"]
)
def get_assigned_employees(
    db: Session = Depends(get_database),
    manager=Depends(require_roles("Manager"))
):
    return db.query(Employee).filter(
        Employee.manager_id == manager.user_id
    ).all()


@app.get(
    "/manager/me/leaves/pending",
    response_model=list[LeaveResponse],
    tags=["Manager"]
)
def get_pending_leaves(
    db: Session = Depends(get_database),
    manager=Depends(require_roles("Manager"))
):
    employee_ids = db.query(Employee.employee_id).filter(
        Employee.manager_id == manager.user_id
    ).subquery()

    return db.query(LeaveRequest).filter(
        LeaveRequest.employee_id.in_(employee_ids),
        LeaveRequest.status == "Pending"
    ).all()


@app.post(
    "/manager/leaves/{leave_id}/review",
    response_model=LeaveResponse,
    tags=["Manager"]
)
def review_leave(
    leave_id: int,
    data: LeaveReview,
    db: Session = Depends(get_database),
    manager=Depends(require_roles("Manager"))
):
    leave = get_leave_or_404(db, leave_id)
    employee = get_employee_or_404(db, leave.employee_id)

    check_manager_access(manager, employee)

    if leave.status != "Pending":
        raise HTTPException(400, "Leave has already been processed")

    leave.status = data.action
    leave.reviewed_by = manager.user_id
    leave.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(leave)

    return leave


# --------------------------------------------------
# FRONTEND
# --------------------------------------------------

@app.get("/", include_in_schema=False)
def login_page():
    return FileResponse("frontend/login.html")


@app.get("/admin-dashboard", include_in_schema=False)
def admin_dashboard():
    return FileResponse("frontend/admin.html")


@app.get("/manager-dashboard", include_in_schema=False)
def manager_dashboard():
    return FileResponse("frontend/manager.html")


@app.get("/employee-dashboard", include_in_schema=False)
def employee_dashboard():
    return FileResponse("frontend/employee.html")


app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)