
const API = "";

// ========================================
// AUTHENTICATION AND TOKEN MANAGEMENT
// ========================================

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function saveTokens(data) {
    localStorage.setItem("access_token", data.access_token);

    if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token);
    }

    if (data.role) {
        localStorage.setItem("role", data.role);
    }
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("role");
    localStorage.removeItem("user_id");
    localStorage.removeItem("full_name");
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
        clearTokens();
        return false;
    }

    try {
        const response = await fetch(`${API}/auth/refresh`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                refresh_token: refreshToken
            })
        });

        if (!response.ok) {
            clearTokens();
            return false;
        }

        const data = await response.json();
        saveTokens(data);

        return true;

    } catch (error) {
        console.error("Token refresh failed:", error);
        return false;
    }
}

async function apiFetch(url, options = {}, retry = true) {
    const headers = new Headers(options.headers || {});

    if (getAccessToken()) {
        headers.set(
            "Authorization",
            `Bearer ${getAccessToken()}`
        );
    }

    if (options.body && !(options.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${API}${url}`, {
        ...options,
        headers
    });

    if (
        response.status === 401 &&
        retry &&
        url !== "/auth/refresh"
    ) {
        const refreshed = await refreshAccessToken();

        if (refreshed) {
            return apiFetch(url, options, false);
        }

        clearTokens();
        window.location.href = "/";

        throw new Error("Session expired. Please login again.");
    }

    return response;
}


// ========================================
// COMMON FUNCTIONS
// ========================================

function showMessage(message, elementId = "message") {
    const element = document.getElementById(elementId);

    if (element) {
        element.textContent = message;
    } else {
        alert(message);
    }
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

async function readResponse(response) {
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
    }

    return data;
}


// ========================================
// DISPLAY TABLE
// ========================================

function displayTable(elementId, rows, columns, actions = false) {
    const element = document.getElementById(elementId);

    if (!element) return;

    if (!rows || rows.length === 0) {
        element.textContent = "No records found.";
        return;
    }

    const headings = columns.map(column =>
        `<th>${escapeHTML(column.label)}</th>`
    ).join("");

    const actionHeading = actions ? "<th>Actions</th>" : "";

    const body = rows.map(row => {
        const cells = columns.map(column =>
            `<td>${escapeHTML(row[column.key])}</td>`
        ).join("");

        const actionButtons = actions
            ? `<td class="action-cell">
                <button
                    type="button"
                    onclick="editEmployee(${Number(row.employee_id)})">
                    Update
                </button>

                <button
                    type="button"
                    class="danger"
                    onclick="deleteEmployee(${Number(row.employee_id)})">
                    Delete
                </button>
               </td>`
            : "";

        return `<tr>${cells}${actionButtons}</tr>`;
    }).join("");

    element.innerHTML = `
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>${headings}${actionHeading}</tr>
                </thead>
                <tbody>${body}</tbody>
            </table>
        </div>
    `;
}


// ========================================
// LOGIN
// ========================================

async function login(event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
        const response = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        const data = await readResponse(response);

        saveTokens(data);

        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("full_name", data.full_name);

        const pages = {
            Admin: "/admin-dashboard",
            Manager: "/manager-dashboard",
            Employee: "/employee-dashboard"
        };

        window.location.href = pages[data.role] || "/";

    } catch (error) {
        showMessage(error.message);
    }
}

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", login);
}


// ========================================
// DASHBOARD ROLE VALIDATION
// ========================================

async function requireDashboard(expectedRole) {
    if (!getAccessToken()) {
        window.location.href = "/";
        return false;
    }

    try {
        const response = await apiFetch("/auth/me");
        const user = await readResponse(response);

        if (user.role !== expectedRole) {
            const pages = {
                Admin: "/admin-dashboard",
                Manager: "/manager-dashboard",
                Employee: "/employee-dashboard"
            };

            window.location.href = pages[user.role] || "/";
            return false;
        }

        return true;

    } catch (error) {
        clearTokens();
        window.location.href = "/";
        return false;
    }
}


// ========================================
// LOGOUT
// ========================================

async function logout() {
    try {
        if (getAccessToken()) {
            await apiFetch("/auth/logout", {
                method: "POST"
            });
        }

    } catch (error) {
        console.error("Logout failed:", error);

    } finally {
        clearTokens();
        window.location.href = "/";
    }
}


// ========================================
// ADMIN - CREATE MANAGER
// ========================================

const managerForm = document.getElementById("managerForm");

if (managerForm) {
    managerForm.addEventListener("submit", async event => {
        event.preventDefault();

        const payload = {
            full_name: document.getElementById("full_name").value.trim(),
            email: document.getElementById("manager_email").value.trim(),
            phone: document.getElementById("manager_phone").value.trim(),
            password: document.getElementById("manager_password").value
        };

        try {
            const response = await apiFetch("/admin/managers", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            await readResponse(response);

            showMessage("Manager created successfully.");

            managerForm.reset();

            await loadManagers();

        } catch (error) {
            showMessage(error.message);
        }
    });
}


// ========================================
// ADMIN - LOAD MANAGERS
// ========================================

async function loadManagers() {
    try {
        const response = await apiFetch("/admin/managers");
        const data = await readResponse(response);

        displayTable("managers", data, [
            { key: "user_id", label: "Manager ID" },
            { key: "full_name", label: "Manager Name" },
            { key: "email", label: "Email" },
            { key: "phone", label: "Phone" },
            { key: "is_active", label: "Active" }
        ]);

        // Fill Manager dropdown
        const managerSelect = document.getElementById("manager_id");

        if (managerSelect) {
            managerSelect.innerHTML =
                '<option value="">Select Manager</option>';

            data.forEach(manager => {
                const option = document.createElement("option");

                option.value = manager.user_id;
                option.textContent =
                    `${manager.full_name} (ID: ${manager.user_id})`;

                managerSelect.appendChild(option);
            });
        }

        showMessage("Managers loaded successfully.");

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// ADMIN - REGISTER EMPLOYEE
// ========================================

const registerEmployeeForm =
    document.getElementById("registerEmployeeForm");

if (registerEmployeeForm) {
    registerEmployeeForm.addEventListener("submit", async event => {
        event.preventDefault();

        const payload = {
            full_name: document.getElementById("employee_name").value.trim(),
            email: document.getElementById("employee_email").value.trim(),
            phone: document.getElementById("employee_phone").value.trim(),
            password: document.getElementById("employee_password").value,
            department: document.getElementById("department").value.trim(),
            designation: document.getElementById("designation").value.trim(),
            manager_id: Number(
                document.getElementById("manager_id").value
            )
        };

        if (!payload.manager_id) {
            showMessage("Please select a Manager.");
            return;
        }

        try {
            const response = await apiFetch(
                "/auth/register-employee",
                {
                    method: "POST",
                    body: JSON.stringify(payload)
                }
            );

            await readResponse(response);

            showMessage("Employee registered successfully.");

            registerEmployeeForm.reset();

            await loadEmployees();

        } catch (error) {
            showMessage(error.message);
        }
    });
}


// ========================================
// ADMIN - LOAD EMPLOYEES
// ========================================

async function loadEmployees() {
    try {
        const response = await apiFetch("/employees");
        const data = await readResponse(response);

        displayTable("employees", data, [
            { key: "employee_id", label: "Employee ID" },
            { key: "employee_name", label: "Employee Name" },
            { key: "email", label: "Email" },
            { key: "phone", label: "Phone" },
            { key: "department", label: "Department" },
            { key: "designation", label: "Designation" },
            { key: "manager_id", label: "Manager ID" }
        ], true);

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// ADMIN - UPDATE EMPLOYEE
// ========================================

async function editEmployee(employeeId) {
    try {
        const response = await apiFetch(
            `/employees/${employeeId}`
        );

        const employee = await readResponse(response);

        let modal = document.getElementById("editEmployeeModal");

        if (!modal) {
            modal = document.createElement("div");
            modal.id = "editEmployeeModal";
            modal.className = "edit-modal";

            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="edit-modal-content">

                <h2>Update Employee</h2>

                <form id="editEmployeeForm">

                    <label for="edit_employee_name">
                        Employee Name
                    </label>

                    <input
                        type="text"
                        id="edit_employee_name"
                        value="${escapeHTML(employee.employee_name)}"
                        required
                    >

                    <label for="edit_email">
                        Email
                    </label>

                    <input
                        type="email"
                        id="edit_email"
                        value="${escapeHTML(employee.email)}"
                        required
                    >

                    <label for="edit_phone">
                        Phone
                    </label>

                    <input
                        type="text"
                        id="edit_phone"
                        value="${escapeHTML(employee.phone)}"
                        required
                    >

                    <label for="edit_department">
                        Department
                    </label>

                    <input
                        type="text"
                        id="edit_department"
                        value="${escapeHTML(employee.department)}"
                        required
                    >

                    <label for="edit_designation">
                        Designation
                    </label>

                    <input
                        type="text"
                        id="edit_designation"
                        value="${escapeHTML(employee.designation)}"
                        required
                    >

                    <div class="edit-buttons">

                        <button type="submit">
                            Save Changes
                        </button>

                        <button
                            type="button"
                            class="danger"
                            onclick="closeEditModal()">
                            Cancel
                        </button>

                    </div>

                </form>

            </div>
        `;

        modal.style.display = "flex";

        const form = document.getElementById("editEmployeeForm");

        form.addEventListener("submit", async event => {
            event.preventDefault();

            const payload = {
                employee_name: document.getElementById(
                    "edit_employee_name"
                ).value.trim(),

                email: document.getElementById(
                    "edit_email"
                ).value.trim(),

                phone: document.getElementById(
                    "edit_phone"
                ).value.trim(),

                department: document.getElementById(
                    "edit_department"
                ).value.trim(),

                designation: document.getElementById(
                    "edit_designation"
                ).value.trim()
            };

            if (Object.values(payload).some(value => !value)) {
                alert("Please fill all fields.");
                return;
            }

            try {
                const updateResponse = await apiFetch(
                    `/employees/${employeeId}`,
                    {
                        method: "PUT",
                        body: JSON.stringify(payload)
                    }
                );

                await readResponse(updateResponse);

                closeEditModal();

                showMessage("Employee updated successfully.");

                await loadEmployees();

            } catch (error) {
                alert("Update failed: " + error.message);
            }
        });

    } catch (error) {
        alert("Could not load employee: " + error.message);
    }
}


// ========================================
// CLOSE UPDATE POPUP
// ========================================

function closeEditModal() {
    const modal = document.getElementById("editEmployeeModal");

    if (modal) {
        modal.style.display = "none";
    }
}


// ========================================
// ADMIN - DELETE EMPLOYEE
// ========================================

async function deleteEmployee(employeeId) {
    const confirmed = confirm(
        "Are you sure you want to delete this employee?"
    );

    if (!confirmed) return;

    try {
        const response = await apiFetch(
            `/employees/${employeeId}`,
            {
                method: "DELETE"
            }
        );

        await readResponse(response);

        showMessage("Employee deleted successfully.");

        await loadEmployees();

    } catch (error) {
        showMessage("Delete failed: " + error.message);
    }
}


// ========================================
// MANAGER - LOAD ASSIGNED EMPLOYEES
// ========================================

async function loadManagerEmployees() {
    try {
        const response = await apiFetch(
            "/manager/me/employees"
        );

        const data = await readResponse(response);

        displayTable("employees", data, [
            { key: "employee_id", label: "Employee ID" },
            { key: "employee_name", label: "Employee Name" },
            { key: "email", label: "Email" },
            { key: "department", label: "Department" },
            { key: "designation", label: "Designation" }
        ]);

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// MANAGER - LOAD PENDING LEAVES
// ========================================

async function loadPendingLeaves() {
    try {
        const response = await apiFetch(
            "/manager/me/leaves/pending"
        );

        const data = await readResponse(response);

        const element = document.getElementById("leaves");

        if (!element) return;

        if (data.length === 0) {
            element.textContent = "No pending leave requests.";
            return;
        }

        element.innerHTML = data.map(leave => `
            <article class="leave-card">

                <p>
                    <strong>Leave ID:</strong>
                    ${escapeHTML(leave.leave_id)}
                </p>

                <p>
                    <strong>Employee ID:</strong>
                    ${escapeHTML(leave.employee_id)}
                </p>

                <p>
                    <strong>From:</strong>
                    ${escapeHTML(leave.from_date)}
                </p>

                <p>
                    <strong>To:</strong>
                    ${escapeHTML(leave.to_date)}
                </p>

                <p>
                    <strong>Type:</strong>
                    ${escapeHTML(leave.leave_type)}
                </p>

                <p>
                    <strong>Reason:</strong>
                    ${escapeHTML(leave.reason)}
                </p>

                <button
                    type="button"
                    onclick="reviewLeave(${Number(leave.leave_id)}, 'Approved')">
                    Approve
                </button>

                <button
                    type="button"
                    class="danger"
                    onclick="reviewLeave(${Number(leave.leave_id)}, 'Rejected')">
                    Reject
                </button>

            </article>
        `).join("");

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// MANAGER - APPROVE OR REJECT LEAVE
// ========================================

async function reviewLeave(leaveId, action) {
    const confirmed = confirm(
        `Are you sure you want to ${action.toLowerCase()} this leave?`
    );

    if (!confirmed) return;

    try {
        const response = await apiFetch(
            `/manager/leaves/${leaveId}/review`,
            {
                method: "POST",
                body: JSON.stringify({
                    action: action
                })
            }
        );

        await readResponse(response);

        showMessage(
            `Leave ${action.toLowerCase()} successfully.`
        );

        await loadPendingLeaves();

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// EMPLOYEE - LOAD MY PROFILE
// ========================================

async function loadMyProfile() {
    try {
        const response = await apiFetch("/employees/me");
        const data = await readResponse(response);

        const element = document.getElementById("profile");

        if (element) {
            element.innerHTML = `
                <p>
                    <strong>Name:</strong>
                    ${escapeHTML(data.employee_name)}
                </p>

                <p>
                    <strong>Email:</strong>
                    ${escapeHTML(data.email)}
                </p>

                <p>
                    <strong>Department:</strong>
                    ${escapeHTML(data.department)}
                </p>

                <p>
                    <strong>Designation:</strong>
                    ${escapeHTML(data.designation)}
                </p>
            `;
        }

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// EMPLOYEE - LOAD MY ATTENDANCE
// ========================================

async function loadMyAttendance() {
    try {
        const response = await apiFetch("/attendance/me");
        const data = await readResponse(response);

        displayTable("attendance", data, [
            { key: "attendance_id", label: "Attendance ID" },
            { key: "attendance_date", label: "Date" },
            { key: "status", label: "Status" }
        ]);

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// EMPLOYEE - LOAD MY LEAVES
// ========================================

async function loadMyLeaves() {
    try {
        const response = await apiFetch("/leaves/me");
        const data = await readResponse(response);

        displayTable("leaves", data, [
            { key: "leave_id", label: "Leave ID" },
            { key: "from_date", label: "From Date" },
            { key: "to_date", label: "To Date" },
            { key: "leave_type", label: "Leave Type" },
            { key: "reason", label: "Reason" },
            { key: "status", label: "Status" }
        ]);

    } catch (error) {
        showMessage(error.message);
    }
}


// ========================================
// EMPLOYEE - APPLY FOR LEAVE
// ========================================

const leaveForm = document.getElementById("leaveForm");

if (leaveForm) {
    leaveForm.addEventListener("submit", async event => {
        event.preventDefault();

        const fromDate =
            document.getElementById("from_date").value;

        const toDate =
            document.getElementById("to_date").value;

        if (!fromDate || !toDate) {
            showMessage("Please select both dates.");
            return;
        }

        if (fromDate > toDate) {
            showMessage("From date cannot be after To date.");
            return;
        }

        const payload = {
            from_date: fromDate,
            to_date: toDate,
            leave_type: document.getElementById("leave_type").value.trim(),
            reason: document.getElementById("reason").value.trim()
        };

        if (!payload.leave_type || !payload.reason) {
            showMessage("Please fill all fields.");
            return;
        }

        try {
            const response = await apiFetch("/leaves", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            await readResponse(response);

            showMessage("Leave applied successfully.");

            leaveForm.reset();

            await loadMyLeaves();

        } catch (error) {
            showMessage(error.message);
        }
    });
}
