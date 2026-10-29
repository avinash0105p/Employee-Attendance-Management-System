from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    phone: str
    role_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateManager(BaseModel):
    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=128)


class RegisterEmployee(BaseModel):
    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=128)
    department: str = Field(min_length=2, max_length=100)
    designation: str = Field(min_length=2, max_length=100)
    manager_id: int = Field(gt=0)


class CreateEmployee(BaseModel):
    employee_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    department: str = Field(min_length=2, max_length=100)
    designation: str = Field(min_length=2, max_length=100)


class UpdateEmployee(CreateEmployee):
    pass


class EmployeeResponse(CreateEmployee):
    employee_id: int
    user_id: int | None = None
    manager_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CreateAttendance(BaseModel):
    employee_id: int = Field(gt=0)
    attendance_date: date
    status: Literal["Present", "Absent", "Half Day", "Leave"]


class UpdateAttendance(CreateAttendance):
    pass


class AttendanceResponse(CreateAttendance):
    attendance_id: int

    model_config = ConfigDict(from_attributes=True)


class CreateLeave(BaseModel):
    employee_id: int | None = Field(default=None, gt=0)
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
    action: Literal["Approved", "Rejected"]