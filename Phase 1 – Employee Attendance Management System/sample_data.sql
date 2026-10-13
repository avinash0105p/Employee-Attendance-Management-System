CREATE DATABASE IF NOT EXISTS employee_attendance_db;

USE employee_attendance_db;


-- Employee table

CREATE TABLE IF NOT EXISTS employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    employee_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    designation VARCHAR(100) NOT NULL
);


-- Attendance table

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE CASCADE
);


-- Leave table

CREATE TABLE IF NOT EXISTS leave_requests (
    leave_id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    leave_type VARCHAR(50) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE CASCADE
);


-- Employees

INSERT INTO employees
(employee_name, email, phone, department, designation)
VALUES
('Avinash', 'avinash@gmail.com', '9876543210', 'IT', 'Python Developer'),
('Rahul', 'rahul@gmail.com', '9876543211', 'HR', 'HR Executive'),
('Priya', 'priya@gmail.com', '9876543212', 'Finance', 'Accountant');


-- Attendance

INSERT INTO attendance
(employee_id, attendance_date, status)
VALUES
(1, '2026-10-08', 'Present'),
(2, '2026-10-08', 'Absent'),
(3, '2026-10-08', 'Leave');


-- Leave Requests

INSERT INTO leave_requests
(employee_id, from_date, to_date, leave_type, reason, status)
VALUES
(1, '2026-10-10', '2026-10-11', 'Casual Leave', 'Personal work', 'Pending'),
(2, '2026-10-15', '2026-10-16', 'Sick Leave', 'Not feeling well', 'Approved'),
(3, '2026-10-20', '2026-10-22', 'Casual Leave', 'Family function', 'Rejected');