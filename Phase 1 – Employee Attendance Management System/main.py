from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_database
from models import Employee, Attendance, LeaveRequest

from schemas import (
    CreateEmployee,
    UpdateEmployee,
    EmployeeResponse,
    CreateAttendance,
    UpdateAttendance,
    CreateLeave,
    UpdateLeave,
    LeaveResponse
)



Base.metadata.create_all(bind=engine)


app = FastAPI(title="Employee Attendance Management System",)

@app.get("/")
def home():
    return {"message": "Employee Attendance Management System"}


# EMPLOYEE MANAGEMENT

# 1. Add Employee
@app.post("/employees", response_model=EmployeeResponse)
def add_employee(
    employee: CreateEmployee,
    db: Session = Depends(get_database)
):
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

        raise HTTPException(
            status_code=400,
            detail="Email or phone number already exists"
        )


# 2. Get All Employees
@app.get("/employees", response_model=list[EmployeeResponse])
def get_all_employees(
    db: Session = Depends(get_database)
):
    employees = db.query(Employee).all()

    return employees


# 3. Get Employee by ID
@app.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_database)
):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee


# 4. Update Employee
@app.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee: UpdateEmployee,
    db: Session = Depends(get_database)
):
    existing_employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if existing_employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    existing_employee.employee_name = employee.employee_name
    existing_employee.email = employee.email
    existing_employee.phone = employee.phone
    existing_employee.department = employee.department
    existing_employee.designation = employee.designation

    try:
        db.commit()
        db.refresh(existing_employee)

        return existing_employee

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Email or phone number already exists"
        )


# 5. Delete Employee
@app.delete("/employees/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_database)
):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    db.delete(employee)
    db.commit()

    return {
        "message": "Employee deleted successfully"
    }


# ATTENDANCE MANAGEMENT

# 6. Mark Attendance
@app.post("/attendance", response_model=UpdateAttendance)
def mark_attendance(
    attendance: CreateAttendance,
    db: Session = Depends(get_database)
):
    employee = db.query(Employee).filter(
        Employee.employee_id == attendance.employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    new_attendance = Attendance(
        employee_id=attendance.employee_id,
        attendance_date=attendance.attendance_date,
        status=attendance.status
    )

    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)

    return new_attendance


# 7. Get All Attendance
@app.get("/attendance", response_model=list[UpdateAttendance])
def get_all_attendance(
    db: Session = Depends(get_database)
):
    attendance = db.query(Attendance).all()

    return attendance


# 8. Get Attendance by Employee ID
@app.get(
    "/attendance/employee/{employee_id}",
    response_model=list[UpdateAttendance]
)
def get_attendance_by_employee(
    employee_id: int,
    db: Session = Depends(get_database)
):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee_id
    ).all()

    return attendance


# 9. Update Attendance
@app.put("/attendance/{attendance_id}", response_model=UpdateAttendance)
def update_attendance(
    attendance_id: int,
    attendance: UpdateAttendance,
    db: Session = Depends(get_database)
):
    existing_attendance = db.query(Attendance).filter(
        Attendance.attendance_id == attendance_id
    ).first()

    if existing_attendance is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found"
        )

    employee = db.query(Employee).filter(
        Employee.employee_id == attendance.employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    existing_attendance.employee_id = attendance.employee_id
    existing_attendance.attendance_date = attendance.attendance_date
    existing_attendance.status = attendance.status

    db.commit()
    db.refresh(existing_attendance)

    return existing_attendance


# 10. Delete Attendance
@app.delete("/attendance/{attendance_id}")
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_database)
):
    attendance = db.query(Attendance).filter(
        Attendance.attendance_id == attendance_id
    ).first()

    if attendance is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found"
        )

    db.delete(attendance)
    db.commit()

    return {
        "message": "Attendance deleted successfully"
    }


# LEAVE MANAGEMENT

# 11. Apply Leave
@app.post("/leaves", response_model=LeaveResponse)
def apply_leave(
    leave: CreateLeave,
    db: Session = Depends(get_database)
):
    employee = db.query(Employee).filter(
        Employee.employee_id == leave.employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    if leave.from_date > leave.to_date:
        raise HTTPException(
            status_code=400,
            detail="From date cannot be greater than To date"
        )

    new_leave = LeaveRequest(
        employee_id=leave.employee_id,
        from_date=leave.from_date,
        to_date=leave.to_date,
        leave_type=leave.leave_type,
        reason=leave.reason,
        status=leave.status
    )

    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)

    return new_leave


# 12. Get All Leave Requests
@app.get("/leaves", response_model=list[LeaveResponse])
def get_all_leaves(
    db: Session = Depends(get_database)
):
    leaves = db.query(LeaveRequest).all()

    return leaves


# 13. Get Leave by ID
@app.get("/leaves/{leave_id}", response_model=LeaveResponse)
def get_leave(
    leave_id: int,
    db: Session = Depends(get_database)
):
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.leave_id == leave_id
    ).first()

    if leave is None:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    return leave


# 14. Update Leave
@app.put("/leaves/{leave_id}", response_model=LeaveResponse)
def update_leave(
    leave_id: int,
    leave: UpdateLeave,
    db: Session = Depends(get_database)
):
    existing_leave = db.query(LeaveRequest).filter(
        LeaveRequest.leave_id == leave_id
    ).first()

    if existing_leave is None:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    employee = db.query(Employee).filter(
        Employee.employee_id == leave.employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    if leave.from_date > leave.to_date:
        raise HTTPException(
            status_code=400,
            detail="From date cannot be greater than To date"
        )

    existing_leave.employee_id = leave.employee_id
    existing_leave.from_date = leave.from_date
    existing_leave.to_date = leave.to_date
    existing_leave.leave_type = leave.leave_type
    existing_leave.reason = leave.reason
    existing_leave.status = leave.status

    db.commit()
    db.refresh(existing_leave)

    return existing_leave


# 15. Delete Leave
@app.delete("/leaves/{leave_id}")
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_database)
):
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.leave_id == leave_id
    ).first()

    if leave is None:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    db.delete(leave)
    db.commit()

    return {
        "message": "Leave request deleted successfully"
    }