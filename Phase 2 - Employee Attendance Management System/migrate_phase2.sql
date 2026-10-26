USE employee_attendance_db;


CREATE TABLE IF NOT EXISTS roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE
);


INSERT IGNORE INTO roles (role_name) VALUES ('Admin'), ('Manager'), ('Employee');


CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

INSERT IGNORE INTO users (full_name, email, phone, password_hash, role_id)
SELECT 
    e.employee_name,
    e.email,
    e.phone,
    'RESET_REQUIRED',
    (SELECT role_id FROM roles WHERE role_name = 'Employee')
FROM employees e;


ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS user_id INT UNIQUE,
ADD COLUMN IF NOT EXISTS manager_id INT NULL;

UPDATE employees e
JOIN users u ON u.email = e.email
SET e.user_id = u.user_id
WHERE e.user_id IS NULL;


ALTER TABLE employees 
ADD CONSTRAINT fk_employees_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_employees_manager FOREIGN KEY (manager_id) REFERENCES users(user_id) ON DELETE SET NULL;


ALTER TABLE leave_requests 
ADD COLUMN IF NOT EXISTS reviewed_by INT NULL,
ADD COLUMN IF NOT EXISTS reviewed_at DATETIME NULL;

ALTER TABLE leave_requests 
ADD CONSTRAINT fk_leave_reviewed_by FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL;

ALTER TABLE leave_requests 
MODIFY status VARCHAR(30) NOT NULL DEFAULT 'Pending';