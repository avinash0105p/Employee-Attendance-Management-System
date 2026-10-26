from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, EmailStr

# Auth & User Schemas
class RegisterEmployee(BaseModel):
    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8)
    department: str = Field(min_length=2, max_length=100)
    designation: str = Field(min_length=2, max_length=100)
    manager_id: int = Field(gt=0)


class CreateManager(BaseModel):
    admin_id: int = Field(gt=0)
    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    phone: str
    role_id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Employee Schemas
class CreateEmployee(BaseModel):
    employee_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    department: str
    designation: str


class UpdateEmployee(CreateEmployee):
    pass


class EmployeeResponse(BaseModel):
    employee_id: int
    employee_name: str
    email: EmailStr
    phone: str
    department: str
    designation: str
    user_id: int | None = None
    manager_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


# Attendance Schemas
class CreateAttendance(BaseModel):
    employee_id: int = Field(gt=0)
    attendance_date: date
    status: Literal["Present", "Absent", "Half Day", "Leave"]


class UpdateAttendance(CreateAttendance):
    pass


class AttendanceResponse(CreateAttendance):
    attendance_id: int
    model_config = ConfigDict(from_attributes=True)


# Leave Schemas
class CreateLeave(BaseModel):
    employee_id: int = Field(gt=0)
    from_date: date
    to_date: date
    leave_type: str = Field(min_length=2, max_length=50)
    reason: str = Field(min_length=2, max_length=500)


class UpdateLeave(BaseModel):
    from_date: date
    to_date: date
    leave_type: str = Field(min_length=2, max_length=50)
    reason: str = Field(min_length=2, max_length=500)


class LeaveResponse(BaseModel):
    leave_id: int
    employee_id: int
    from_date: date
    to_date: date
    leave_type: str
    reason: str
    status: Literal["Pending", "Approved", "Rejected"]
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class LeaveReview(BaseModel):
    manager_id: int = Field(gt=0)
    action: Literal["Approved", "Rejected"]