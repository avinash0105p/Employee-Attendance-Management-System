const API = "";

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function saveTokens(data) {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("role", data.role);
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
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            clearTokens();
            return false;
        }

        const data = await response.json();
        saveTokens(data);
        return true;
    } catch {
        return false;
    }
}

async function apiFetch(url, options = {}, retry = true) {
    const headers = new Headers(options.headers || {});

    if (getAccessToken()) {
        headers.set("Authorization", `Bearer ${getAccessToken()}`);
    }

    if (options.body && !(options.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
    }

    let response = await fetch(`${API}${url}`, {
        ...options,
        headers
    });

    if (response.status === 401 && retry && url !== "/auth/refresh") {
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

function showMessage(message, elementId = "message") {
    const element = document.getElementById(elementId);

    if (element) {
        element.textContent = message;
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

function displayTable(elementId, rows, columns) {
    const element = document.getElementById(elementId);

    if (!element) return;

    if (!rows || rows.length === 0) {
        element.textContent = "No records found.";
        return;
    }

    const headings = columns.map(column =>
        `<th>${escapeHTML(column.label)}</th>`
    ).join("");

    const body = rows.map(row => `
        <tr>
            ${columns.map(column =>
                `<td>${escapeHTML(row[column.key])}</td>`
            ).join("")}
        </tr>
    `).join("");

    element.innerHTML = `
        <div class="table-wrapper">
            <table>
                <thead><tr>${headings}</tr></thead>
                <tbody>${body}</tbody>
            </table>
        </div>
    `;
}

async function login(event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
        const response = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed");
        }

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

async function requireDashboard(expectedRole) {
    if (!getAccessToken()) {
        window.location.href = "/";
        return;
    }

    try {
        const response = await apiFetch("/auth/me");

        if (!response.ok) {
            clearTokens();
            window.location.href = "/";
            return;
        }

        const user = await response.json();

        if (user.role !== expectedRole) {
            const pages = {
                Admin: "/admin-dashboard",
                Manager: "/manager-dashboard",
                Employee: "/employee-dashboard"
            };

            window.location.href = pages[user.role] || "/";
        }
    } catch {
        window.location.href = "/";
    }
}

async function logout() {
    try {
        if (getAccessToken()) {
            await apiFetch("/auth/logout", { method: "POST" });
        }
    } catch (error) {
        console.error("Logout request failed:", error);
    } finally {
        clearTokens();
        window.location.href = "/";
    }
}


// ADMIN

const managerForm = document.getElementById("managerForm");

if (managerForm) {
    managerForm.addEventListener("submit", async event => {
        event.preventDefault();

        const payload = {
            full_name: document.getElementById("full_name").value.trim(),
            email: document.getElementById("manager_email").value.trim(),
            phone: document.getElementById("phone").value.trim(),
            password: document.getElementById("manager_password").value
        };

        try {
            const response = await apiFetch("/admin/managers", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Could not create Manager");
            }

            showMessage("Manager created successfully.");
            managerForm.reset();
        } catch (error) {
            showMessage(error.message);
        }
    });
}

async function loadEmployees() {
    try {
        const response = await apiFetch("/employees");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not load employees");
        }

        displayTable("employees", data, [
            { key: "employee_id", label: "ID" },
            { key: "employee_name", label: "Name" },
            { key: "email", label: "Email" },
            { key: "phone", label: "Phone" },
            { key: "department", label: "Department" },
            { key: "designation", label: "Designation" },
            { key: "manager_id", label: "Manager ID" }
        ]);
    } catch (error) {
        showMessage(error.message);
    }
}


// MANAGER

async function loadManagerEmployees() {
    try {
        const response = await apiFetch("/manager/me/employees");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not load employees");
        }

        displayTable("employees", data, [
            { key: "employee_id", label: "ID" },
            { key: "employee_name", label: "Name" },
            { key: "email", label: "Email" },
            { key: "department", label: "Department" },
            { key: "designation", label: "Designation" }
        ]);
    } catch (error) {
        showMessage(error.message);
    }
}

async function loadPendingLeaves() {
    try {
        const response = await apiFetch("/manager/me/leaves/pending");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not load leave requests");
        }

        const element = document.getElementById("leaves");

        if (!element) return;

        if (data.length === 0) {
            element.textContent = "No pending leave requests.";
            return;
        }

        element.innerHTML = data.map(leave => `
            <article class="leave-card">
                <p><strong>Leave ID:</strong> ${escapeHTML(leave.leave_id)}</p>
                <p><strong>Employee ID:</strong> ${escapeHTML(leave.employee_id)}</p>
                <p><strong>Dates:</strong>
                    ${escapeHTML(leave.from_date)} to ${escapeHTML(leave.to_date)}
                </p>
                <p><strong>Type:</strong> ${escapeHTML(leave.leave_type)}</p>
                <p><strong>Reason:</strong> ${escapeHTML(leave.reason)}</p>
                <button onclick="reviewLeave(${Number(leave.leave_id)}, 'Approved')">
                    Approve
                </button>
                <button class="danger"
                    onclick="reviewLeave(${Number(leave.leave_id)}, 'Rejected')">
                    Reject
                </button>
            </article>
        `).join("");
    } catch (error) {
        showMessage(error.message);
    }
}

async function reviewLeave(leaveId, action) {
    try {
        const response = await apiFetch(
            `/manager/leaves/${leaveId}/review`,
            {
                method: "POST",
                body: JSON.stringify({ action })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Leave review failed");
        }

        showMessage(`Leave ${action.toLowerCase()} successfully.`);
        await loadPendingLeaves();
    } catch (error) {
        showMessage(error.message);
    }
}


// EMPLOYEE

async function loadMyProfile() {
    try {
        const response = await apiFetch("/employees/me");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not load profile");
        }

        const element = document.getElementById("profile");

        if (element) {
            element.innerHTML = `
                <p><strong>Name:</strong> ${escapeHTML(data.employee_name)}</p>
                <p><strong>Email:</strong> ${escapeHTML(data.email)}</p>
                <p><strong>Department:</strong> ${escapeHTML(data.department)}</p>
                <p><strong>Designation:</strong> ${escapeHTML(data.designation)}</p>
            `;
        }
    } catch (error) {
        showMessage(error.message);
    }
}

async function loadMyAttendance() {
    try {
        const response = await apiFetch("/attendance/me");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not load attendance");
        }

        displayTable("attendance", data, [
            { key: "attendance_date", label: "Date" },
            { key: "status", label: "Status" }
        ]);
    } catch (error) {
        showMessage(error.message);
    }
}

async function loadMyLeaves() {
    try {
        const response = await apiFetch("/leaves/me");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not load leave status");
        }

        displayTable("leaves", data, [
            { key: "leave_id", label: "ID" },
            { key: "from_date", label: "From" },
            { key: "to_date", label: "To" },
            { key: "leave_type", label: "Type" },
            { key: "reason", label: "Reason" },
            { key: "status", label: "Status" }
        ]);
    } catch (error) {
        showMessage(error.message);
    }
}

const leaveForm = document.getElementById("leaveForm");

if (leaveForm) {
    leaveForm.addEventListener("submit", async event => {
        event.preventDefault();

        const fromDate = document.getElementById("from_date").value;
        const toDate = document.getElementById("to_date").value;

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

        try {
            const response = await apiFetch("/leaves", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Leave application failed");
            }

            showMessage("Leave applied successfully.");
            leaveForm.reset();
            await loadMyLeaves();
        } catch (error) {
            showMessage(error.message);
        }
    });
}