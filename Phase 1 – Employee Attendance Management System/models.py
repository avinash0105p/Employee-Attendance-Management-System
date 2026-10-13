
'''
These are the SQLAlchemy models.
Each class represents one MySQL table.
'''

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from database import Base

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key = True, autoincrement = True)
    employee_name = Column(String(50), nullable = False)
    email = Column(String(50), nullable = False, unique = True)
    phone = Column(String(10), nullable = False, unique = True)
    department = Column(String(50), nullable = False)
    designation = Column(String(50), nullable = False)

class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(Integer, primary_key = True, autoincrement = True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete = "CASCADE"), nullable = False)
    attendance_date = Column(Date, nullable = False)
    status = Column(String(50), nullable = False)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    leave_id = Column(Integer, primary_key = True, index = True,  autoincrement = True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete = "CASCADE"), nullable = False)
    from_date = Column(Date, nullable = False)
    to_date = Column(Date, nullable = False)
    leave_type = Column(String(50), nullable = False)
    reason = Column(String(500), nullable = False)
    status = Column(String(50), nullable = False)