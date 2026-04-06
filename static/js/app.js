const pageName = document.body.dataset.page;
let currentSession = null;
let cachedTaxes = [];
let cachedTaxpayers = [];
let cachedProperties = [];

// This function shows Bootstrap alerts on every page.
function showAlert(message, type = "success") {
    const alertBox = document.getElementById("alertBox");
    if (!alertBox) {
        return;
    }

    alertBox.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

async function apiRequest(url, options = {}) {
    // This helper keeps all fetch calls in one reusable place.
    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        credentials: "same-origin",
        ...options,
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || "Request failed.");
    }
    return data;
}

function formatCurrency(value) {
    return `₹ ${Number(value || 0).toFixed(2)}`;
}

function formatDate(value) {
    if (!value) {
        return "-";
    }

    return new Date(value).toLocaleString();
}

function statusBadge(status) {
    const normalized = (status || "").toUpperCase();
    if (normalized === "PAID" || normalized === "SUCCESS") {
        return '<span class="badge badge-soft-success">Paid</span>';
    }
    if (normalized === "PARTIAL") {
        return '<span class="badge badge-soft-warning">Partial</span>';
    }
    return '<span class="badge badge-soft-danger">Pending</span>';
}

async function loadSession() {
    try {
        // Session data helps the same script support both admin and taxpayer pages.
        const data = await apiRequest("/api/auth/session");
        currentSession = data.authenticated ? data.user : null;
        return currentSession;
    } catch (error) {
        currentSession = null;
        return null;
    }
}

function updateUserBadge() {
    const userBadge = document.getElementById("userBadge");
    const logoutButton = document.getElementById("logoutButton");
    const mainNav = document.getElementById("mainNav");

    if (!userBadge || !logoutButton || !mainNav) {
        return;
    }

    if (currentSession) {
        userBadge.textContent = `${currentSession.name} (${currentSession.role})`;
        logoutButton.classList.remove("d-none");
    } else {
        userBadge.textContent = "Welcome";
        logoutButton.classList.add("d-none");
    }

    if (currentSession?.role !== "admin") {
        mainNav.querySelector('a[href="/properties"]').textContent = "Property Details";
    }
}

function protectAuthenticatedPages() {
    const publicPages = ["login", "register"];
    if (publicPages.includes(pageName)) {
        if (currentSession) {
            window.location.href = "/dashboard";
        }
        return false;
    }

    if (!currentSession) {
        window.location.href = "/login";
        return true;
    }

    return false;
}

async function handleLogout() {
    await apiRequest("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
}

async function initializeLoginPage() {
    const form = document.getElementById("loginForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            const payload = {
                role: document.getElementById("loginRole").value,
                email: document.getElementById("loginEmail").value,
                password: document.getElementById("loginPassword").value,
            };
            const data = await apiRequest("/api/auth/login", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            showAlert(data.message, "success");
            window.location.href = "/dashboard";
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });
}

async function initializeRegisterPage() {
    const form = document.getElementById("registerForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            const payload = {
                full_name: document.getElementById("registerName").value,
                phone: document.getElementById("registerPhone").value,
                email: document.getElementById("registerEmail").value,
                address: document.getElementById("registerAddress").value,
                password: document.getElementById("registerPassword").value,
            };
            const data = await apiRequest("/api/auth/register", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            showAlert(data.message, "success");
            setTimeout(() => {
                window.location.href = "/login";
            }, 1200);
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });
}

function renderRecentPayments(payments) {
    const body = document.getElementById("recentPaymentsBody");
    if (!body) {
        return;
    }

    if (!payments.length) {
        body.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No payments found.</td></tr>';
        return;
    }

    body.innerHTML = payments
        .map(
            (item) => `
                <tr>
                    <td>${item.payment_reference}</td>
                    <td>${formatCurrency(item.amount_paid)}</td>
                    <td>${item.payment_method}</td>
                    <td>${statusBadge(item.payment_status)}</td>
                    <td>${formatDate(item.paid_at)}</td>
                </tr>
            `
        )
        .join("");
}

function renderReportSummary(monthlyRows) {
    const box = document.getElementById("reportSummaryBox");
    if (!box) {
        return;
    }

    if (!monthlyRows.length) {
        box.innerHTML = "No monthly collection data available.";
        return;
    }

    box.innerHTML = monthlyRows
        .map(
            (item) => `
                <div class="border rounded p-2 mb-2">
                    <div class="fw-semibold">${item.collection_month}</div>
                    <div>Payments: ${item.payment_count}</div>
                    <div>Total Collection: ${formatCurrency(item.total_amount)}</div>
                </div>
            `
        )
        .join("");
}

async function initializeDashboardPage() {
    try {
        // The dashboard shows different summary numbers for admin and taxpayer roles.
        const data = await apiRequest("/api/dashboard/summary");
        const summary = data.summary || {};

        if (currentSession.role === "admin") {
            document.getElementById("summaryProperties").textContent = summary.property_count || 0;
            document.getElementById("summaryTaxes").textContent = summary.taxpayer_count || 0;
            document.getElementById("summaryCollection").textContent = formatCurrency(summary.total_collection || 0);
            document.getElementById("summaryPending").textContent = summary.pending_tax_count || 0;
        } else {
            document.getElementById("summaryProperties").textContent = summary.property_count || 0;
            document.getElementById("summaryTaxes").textContent = summary.tax_count || 0;
            document.getElementById("summaryCollection").textContent = formatCurrency(summary.total_paid || 0);
            document.getElementById("summaryPending").textContent = summary.pending_tax_count || 0;
        }

        renderRecentPayments(data.recent_payments || []);

        const reportButton = document.getElementById("loadReportsButton");
        if (currentSession.role === "admin" && reportButton) {
            reportButton.classList.remove("d-none");
            reportButton.addEventListener("click", async () => {
                const reportData = await apiRequest("/api/reports/collection");
                renderReportSummary(reportData.monthly_summary || []);
            });
        }
    } catch (error) {
        showAlert(error.message, "danger");
    }
}

function resetPropertyForm() {
    // Resetting the form makes it easy to switch from edit mode to add mode.
    document.getElementById("propertyId").value = "";
    document.getElementById("propertyCode").value = "";
    document.getElementById("propertyTaxpayer").value = "";
    document.getElementById("propertyType").value = "Residential";
    document.getElementById("propertyAddress").value = "";
    document.getElementById("propertyArea").value = "";
    document.getElementById("propertyValue").value = "";
    document.getElementById("propertyFormTitle").textContent = "Add Property";
}

function togglePropertyForm(show) {
    const card = document.getElementById("propertyFormCard");
    if (!card) {
        return;
    }
    card.classList.toggle("d-none", !show);
}

function fillTaxpayerOptions() {
    const taxpayerSelect = document.getElementById("propertyTaxpayer");
    if (!taxpayerSelect) {
        return;
    }

    taxpayerSelect.innerHTML = '<option value="">Select taxpayer</option>' +
        cachedTaxpayers
            .map((taxpayer) => `<option value="${taxpayer.id}">${taxpayer.full_name} (${taxpayer.email})</option>`)
            .join("");
}

function startEditProperty(property) {
    document.getElementById("propertyId").value = property.id;
    document.getElementById("propertyCode").value = property.property_code;
    document.getElementById("propertyTaxpayer").value = property.taxpayer_id;
    document.getElementById("propertyType").value = property.property_type;
    document.getElementById("propertyAddress").value = property.address;
    document.getElementById("propertyArea").value = property.area_sqft;
    document.getElementById("propertyValue").value = property.property_value;
    document.getElementById("propertyFormTitle").textContent = "Edit Property";
    togglePropertyForm(true);
}

function renderPropertyTable() {
    const body = document.getElementById("propertyTableBody");
    const actionHeader = document.getElementById("propertyActionHeader");
    if (!body) {
        return;
    }

    if (currentSession.role !== "admin" && actionHeader) {
        actionHeader.textContent = "Status";
    }

    if (!cachedProperties.length) {
        body.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No properties found.</td></tr>';
        return;
    }

    body.innerHTML = cachedProperties
        .map((property) => {
            const actionCell = currentSession.role === "admin"
                ? `
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="startEditPropertyById(${property.id})">Edit</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deletePropertyById(${property.id})">Delete</button>
                `
                : '<span class="badge bg-info-subtle text-dark">Registered</span>';

            return `
                <tr>
                    <td>${property.property_code}</td>
                    <td>${property.taxpayer_name}</td>
                    <td>${property.property_type}</td>
                    <td>${property.area_sqft}</td>
                    <td>${formatCurrency(property.property_value)}</td>
                    <td>${property.address}</td>
                    <td>${actionCell}</td>
                </tr>
            `;
        })
        .join("");
}

window.startEditPropertyById = function (propertyId) {
    const selectedProperty = cachedProperties.find((item) => item.id === propertyId);
    if (selectedProperty) {
        startEditProperty(selectedProperty);
    }
};

window.deletePropertyById = async function (propertyId) {
    if (!confirm("Are you sure you want to delete this property?")) {
        return;
    }

    try {
        const data = await apiRequest(`/api/properties/${propertyId}`, { method: "DELETE" });
        showAlert(data.message, "success");
        await initializePropertiesPage();
    } catch (error) {
        showAlert(error.message, "danger");
    }
};

async function initializePropertiesPage() {
    try {
        const data = await apiRequest("/api/properties");
        cachedProperties = data.properties || [];
        cachedTaxpayers = data.taxpayers || [];
        renderPropertyTable();

        const newPropertyButton = document.getElementById("newPropertyButton");
        const formCard = document.getElementById("propertyFormCard");

        if (currentSession.role === "admin") {
            fillTaxpayerOptions();
            newPropertyButton.classList.remove("d-none");
            newPropertyButton.onclick = () => {
                resetPropertyForm();
                togglePropertyForm(true);
            };
        } else if (formCard) {
            formCard.classList.add("d-none");
        }
    } catch (error) {
        showAlert(error.message, "danger");
    }
}

function renderTaxes() {
    const body = document.getElementById("taxTableBody");
    const select = document.getElementById("paymentTaxId");
    if (!body || !select) {
        return;
    }

    if (!cachedTaxes.length) {
        body.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No tax records found.</td></tr>';
        select.innerHTML = '<option value="">No payable tax available</option>';
        return;
    }

    body.innerHTML = cachedTaxes
        .map(
            (tax) => `
                <tr>
                    <td>${tax.property_code}<br><small class="text-muted">${tax.address}</small></td>
                    <td>${tax.tax_year}</td>
                    <td>${formatCurrency(tax.base_tax)}</td>
                    <td>${formatCurrency(tax.penalty_amount)}</td>
                    <td>${formatCurrency(tax.total_due)}</td>
                    <td>${formatCurrency(tax.amount_paid)}</td>
                    <td>${formatCurrency(tax.balance_due)}</td>
                    <td>${statusBadge(tax.status)}</td>
                </tr>
            `
        )
        .join("");

    const payableTaxes = cachedTaxes.filter((tax) => Number(tax.balance_due) > 0);
    // Only unpaid or partially paid taxes appear in the payment dropdown.
    select.innerHTML = '<option value="">Select tax record</option>' +
        payableTaxes
            .map(
                (tax) => `
                    <option value="${tax.id}">
                        ${tax.property_code} - ${tax.tax_year} - Balance ${formatCurrency(tax.balance_due)}
                    </option>
                `
            )
            .join("");
}

async function initializePaymentPage() {
    try {
        const data = await apiRequest("/api/taxes");
        cachedTaxes = data.taxes || [];
        renderTaxes();
    } catch (error) {
        showAlert(error.message, "danger");
    }
}

async function initializeHistoryPage() {
    try {
        const data = await apiRequest("/api/payments/history");
        const body = document.getElementById("paymentHistoryBody");

        if (!data.payments.length) {
            body.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No payment history available.</td></tr>';
            return;
        }

        body.innerHTML = data.payments
            .map(
                (payment) => `
                    <tr>
                        <td>${payment.payment_reference}</td>
                        <td>${payment.property_code}</td>
                        <td>${payment.taxpayer_name}</td>
                        <td>${payment.tax_year}</td>
                        <td>${payment.payment_method}</td>
                        <td>${formatCurrency(payment.amount_paid)}</td>
                        <td>${statusBadge(payment.payment_status)}</td>
                        <td>${formatDate(payment.paid_at)}</td>
                    </tr>
                `
            )
            .join("");
    } catch (error) {
        showAlert(error.message, "danger");
    }
}

function bindPropertyEvents() {
    const form = document.getElementById("propertyForm");
    const cancelButton = document.getElementById("cancelPropertyButton");

    if (!form || !cancelButton) {
        return;
    }

    cancelButton.addEventListener("click", () => {
        resetPropertyForm();
        togglePropertyForm(false);
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const propertyId = document.getElementById("propertyId").value;
        const payload = {
            property_code: document.getElementById("propertyCode").value,
            taxpayer_id: document.getElementById("propertyTaxpayer").value,
            property_type: document.getElementById("propertyType").value,
            address: document.getElementById("propertyAddress").value,
            area_sqft: document.getElementById("propertyArea").value,
            property_value: document.getElementById("propertyValue").value,
        };

        try {
            const data = await apiRequest(propertyId ? `/api/properties/${propertyId}` : "/api/properties", {
                method: propertyId ? "PUT" : "POST",
                body: JSON.stringify(payload),
            });
            showAlert(data.message, "success");
            resetPropertyForm();
            togglePropertyForm(false);
            await initializePropertiesPage();
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });
}

function bindPaymentEvents() {
    const form = document.getElementById("paymentForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            // The form sends the selected tax id and amount to the payment API.
            const payload = {
                tax_id: document.getElementById("paymentTaxId").value,
                amount_paid: document.getElementById("paymentAmount").value,
                payment_method: document.getElementById("paymentMethod").value,
            };
            const data = await apiRequest("/api/payments", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            showAlert(`${data.message} Reference: ${data.payment_reference}`, "success");
            form.reset();
            await initializePaymentPage();
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadSession();

    if (protectAuthenticatedPages()) {
        return;
    }

    updateUserBadge();

    const logoutButton = document.getElementById("logoutButton");
    if (logoutButton) {
        logoutButton.addEventListener("click", handleLogout);
    }

    if (pageName === "login") {
        initializeLoginPage();
    } else if (pageName === "register") {
        initializeRegisterPage();
    } else if (pageName === "dashboard") {
        initializeDashboardPage();
    } else if (pageName === "properties") {
        bindPropertyEvents();
        initializePropertiesPage();
    } else if (pageName === "payment") {
        bindPaymentEvents();
        initializePaymentPage();
    } else if (pageName === "history") {
        initializeHistoryPage();
    }
});
