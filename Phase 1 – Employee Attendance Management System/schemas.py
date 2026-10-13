#Pydantic schemas are used for input validation and API responses.

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict



class CreateEmployee(BaseModel):
    employee_name : str = Field(min_length = 3, max_length = 100)
    email : str
    phone : str = Field(min_length = 10, max_length = 10)
    department :str
    designation : str


class UpdateEmployee(BaseModel):
    employee_name : str = Field(min_length = 3, max_length = 100)
    email : str
    phone : str = Field(min_length = 10, max_length = 10)
    department :str
    designation : str

class EmployeeResponse(CreateEmployee):
    employee_id : int
    model_config = ConfigDict(from_attributes = True)

#attendance

class CreateAttendance(BaseModel):
    employee_id : int
    attendance_date : date
    status : Literal["Present", "Absent", "Leave"]


class UpdateAttendance(CreateAttendance):
    attendance_id : int
    model_config = ConfigDict(from_attributes = True)


#leaves

class CreateLeave(BaseModel):
    employee_id : int
    from_date : date
    to_date : date
    leave_type : str
    reason : str
    status : Literal["Pending", "Approved", "Rejected"] = "Pending"

class UpdateLeave(CreateLeave):
    employee_id : int
    from_date : date
    to_date : date
    leave_type : str
    reason : str
    status : Literal["Pending", "Approved", "Rejected"]

class LeaveResponse(CreateLeave):
    leave_id : int
    model_config = ConfigDict(from_attributes = True)