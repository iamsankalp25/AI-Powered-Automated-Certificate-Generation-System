const API_URL = "http://127.0.0.1:5000";

const fileInput = document.getElementById("fileInput");
const uploadArea = document.getElementById("uploadArea");

const fileName = document.getElementById("fileName");
const results = document.getElementById("results");
const recordCount = document.getElementById("recordCount");

const validation = document.getElementById("validation");
const tableBody = document.getElementById("tableBody");

const generateButton = document.getElementById("generateButton");

let uploadedData = [];


/* ==========================================
   FILE SELECTION
========================================== */

fileInput.addEventListener("change", function () {

    if (!fileInput.files || fileInput.files.length === 0) {
        return;
    }

    const file = fileInput.files[0];

    // Immediately show selected filename
    fileName.textContent = `Uploading ${file.name}...`;

    uploadFile(file);
});


/* ==========================================
   DRAG & DROP
========================================== */

uploadArea.addEventListener("dragover", function (event) {

    event.preventDefault();

    uploadArea.classList.add("dragging");
});


uploadArea.addEventListener("dragleave", function () {

    uploadArea.classList.remove("dragging");
});


uploadArea.addEventListener("drop", function (event) {

    event.preventDefault();

    uploadArea.classList.remove("dragging");

    const files = event.dataTransfer.files;

    if (!files || files.length === 0) {
        return;
    }

    const file = files[0];

    // Show filename immediately
    fileName.textContent = `Uploading ${file.name}...`;

    uploadFile(file);
});


/* ==========================================
   UPLOAD FILE
========================================== */

async function uploadFile(file) {

    validation.innerHTML = `
        <div class="validation-message">
            Uploading and validating <strong>${escapeHTML(file.name)}</strong>...
        </div>
    `;

    generateButton.disabled = true;

    const formData = new FormData();

    formData.append("file", file);

    try {

        const response = await fetch(
            `${API_URL}/api/upload-excel`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        console.log("Upload response:", data);

        if (!response.ok || !data.success) {

            throw new Error(
                data.message || "Excel upload failed"
            );
        }

        uploadedData = data.records || [];

        // Show filename
        fileName.textContent = file.name;

        // Show number of records
        recordCount.textContent =
            `${uploadedData.length} record${uploadedData.length !== 1 ? "s" : ""}`;

        // Show results section
        results.style.display = "block";

        // Display table
        displayTable(uploadedData);

        // Validation result
        if (data.valid) {

            validation.innerHTML = `
                <div class="validation-message success">
                    ✓ File uploaded and validated successfully
                </div>
            `;

            generateButton.disabled = false;

        } else {

            validation.innerHTML = `
                <div class="validation-message error">
                    ⚠ ${formatErrors(data.errors)}
                </div>
            `;

            generateButton.disabled = true;
        }

    } catch (error) {

        console.error("Upload error:", error);

        fileName.textContent = file.name;

        recordCount.textContent = "0 records";

        validation.innerHTML = `
            <div class="validation-message error">
                ⚠ ${escapeHTML(error.message)}
            </div>
        `;

        generateButton.disabled = true;
    }
}


/* ==========================================
   DISPLAY TABLE
========================================== */

function displayTable(records) {

    tableBody.innerHTML = "";

    records.forEach(function (record, index) {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${index + 1}</td>

            <td>
                ${escapeHTML(record.Name)}
            </td>

            <td>
                ${escapeHTML(record.Event)}
            </td>

            <td>
                ${escapeHTML(record.Organization)}
            </td>

            <td>
                ${escapeHTML(record.Date)}
            </td>

            <td>
                ${escapeHTML(record.Achievement)}
            </td>
        `;

        tableBody.appendChild(row);
    });
}


/* ==========================================
   GENERATE CERTIFICATES
========================================== */

generateButton.addEventListener(
    "click",
    generateCertificates
);


async function generateCertificates() {

    if (uploadedData.length === 0) {

        validation.innerHTML = `
            <div class="validation-message error">
                ⚠ Please upload an Excel file first.
            </div>
        `;

        return;
    }

    generateButton.disabled = true;

    generateButton.textContent =
        "Generating Certificates...";

    validation.innerHTML = `
        <div class="validation-message">
            Creating ${uploadedData.length} certificates. Please wait...
        </div>
    `;

    try {

        const response = await fetch(
            `${API_URL}/api/generate-certificates`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            }
        );

        const data = await response.json();

        console.log("Generation response:", data);

        if (!response.ok || !data.success) {

            throw new Error(
                data.message ||
                "Certificate generation failed"
            );
        }

        validation.innerHTML = `
            <div class="validation-message success">
                ✓ ${data.total_certificates} certificates generated successfully.
                Your ZIP download should start automatically.
            </div>
        `;

        // Download ZIP
        const downloadURL =
            `${API_URL}${data.download_url}`;

        const link = document.createElement("a");

        link.href = downloadURL;

        link.download = "certificates.zip";

        document.body.appendChild(link);

        link.click();

        document.body.removeChild(link);

    } catch (error) {

        console.error(
            "Certificate generation error:",
            error
        );

        validation.innerHTML = `
            <div class="validation-message error">
                ⚠ ${escapeHTML(error.message)}
            </div>
        `;

    } finally {

        generateButton.disabled = false;

        generateButton.textContent =
            "✦ Generate Certificates →";
    }
}


/* ==========================================
   FORMAT ERRORS
========================================== */

function formatErrors(errors) {

    if (!errors || errors.length === 0) {
        return "The Excel file contains invalid data.";
    }

    return errors
        .map(error => escapeHTML(error))
        .join("<br>");
}


/* ==========================================
   HTML ESCAPE
========================================== */

function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}