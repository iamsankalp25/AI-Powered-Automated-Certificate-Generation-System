
import uuid
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from excel_processor import (
    read_excel,
    validate_columns,
    validate_data,
)
from certificate_generator import generate_bulk_certificates
from database import (
    initialize_database,
    get_all_certificates,
    get_certificate,
    get_connection,
)


app = Flask(__name__)
CORS(app)


# --------------------------------------------------
# Folders and configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "uploads"
GENERATED_FOLDER = BASE_DIR / "generated"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
GENERATED_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_TEMPLATES = {"classic", "modern", "elegant"}

# Store the most recently uploaded Excel records.
uploaded_records = []
uploaded_batch_token = None

# Initialize SQLite database.
initialize_database()


# --------------------------------------------------
# Home route
# --------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "CertiAI Backend is running",
    })


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "running",
    })


# --------------------------------------------------
# Upload Excel or CSV file
# --------------------------------------------------

@app.route("/api/upload-excel", methods=["POST"])
def upload_excel():
    global uploaded_records, uploaded_batch_token

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "message": "No file uploaded",
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "success": False,
            "message": "No file selected",
        }), 400

    extension = Path(file.filename).suffix.lower()

    if extension not in {".xlsx", ".xls", ".csv"}:
        return jsonify({
            "success": False,
            "message": "Only Excel or CSV files are allowed",
        }), 400

    unique_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    file_path = UPLOAD_FOLDER / unique_name
    file.save(file_path)

    try:
        records = read_excel(str(file_path))

        column_errors = validate_columns(records)

        if column_errors:
            return jsonify({
                "success": False,
                "message": "Invalid Excel columns",
                "errors": column_errors,
            }), 400

        validation_errors = validate_data(records)

        uploaded_records = records
        uploaded_batch_token = uuid.uuid4().hex

        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "filename": file.filename,
            "total_records": len(records),
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "records": records,
        })

    except Exception as error:
        app.logger.exception("Excel processing failed")

        return jsonify({
            "success": False,
            "message": f"Error processing file: {str(error)}",
        }), 500


# --------------------------------------------------
# Generate certificates and save to SQLite
# --------------------------------------------------

@app.route("/api/generate-certificates", methods=["POST"])
def generate_certificates():
    global uploaded_records, uploaded_batch_token

    if not uploaded_records:
        return jsonify({
            "success": False,
            "message": "Please upload an Excel file first",
        }), 400

    if not uploaded_batch_token:
        return jsonify({
            "success": False,
            "message": "Please upload the Excel file again",
        }), 400

    # Read the selected template from the frontend.
    data = request.get_json(silent=True) or {}

    template = data.get("template", "classic")

    if not isinstance(template, str):
        template = "classic"

    template = template.strip().lower()

    if template not in ALLOWED_TEMPLATES:
        return jsonify({
            "success": False,
            "message": "Invalid template selected",
            "allowed_templates": sorted(ALLOWED_TEMPLATES),
        }), 400

    # Validate participant data.
    validation_errors = validate_data(uploaded_records)

    if validation_errors:
        return jsonify({
            "success": False,
            "message": "Please correct the invalid participant data",
            "errors": validation_errors,
        }), 400

    batch_id = uploaded_batch_token
    output_folder = GENERATED_FOLDER / batch_id
    output_folder.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Assign a unique ID to every certificate.
        records_with_ids = []

        for record in uploaded_records:
            updated_record = dict(record)

            updated_record["certificate_id"] = (
                uuid.uuid4().hex[:12].upper()
            )

            records_with_ids.append(updated_record)

        # Step 2: Generate PDFs using the selected template.
        zip_path, generated_files = generate_bulk_certificates(
            records_with_ids,
            str(output_folder),
            template=template,
        )

        if len(generated_files) != len(records_with_ids):
            raise RuntimeError(
                "Not all certificates were generated"
            )

        # Step 3: Save certificate records to SQLite.
        # The IDs saved here match those printed in the PDFs.
        with get_connection() as connection:
            for record in records_with_ids:
                connection.execute(
                    """
                    INSERT INTO certificates (
                        certificate_id,
                        participant_name,
                        event,
                        organization,
                        certificate_date,
                        achievement,
                        generated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["certificate_id"],
                        str(record["Name"]).strip(),
                        str(record["Event"]).strip(),
                        str(record["Organization"]).strip(),
                        str(record["Date"]).strip(),
                        str(record["Achievement"]).strip(),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )

        return jsonify({
            "success": True,
            "message": (
                f"Certificates generated successfully "
                f"using the {template} template"
            ),
            "template": template,
            "total_certificates": len(generated_files),
            "download_url": f"/api/download/{batch_id}",
        })

    except Exception as error:
        app.logger.exception("Certificate generation failed")

        return jsonify({
            "success": False,
            "message": (
                f"Certificate generation failed: {str(error)}"
            ),
        }), 500


# --------------------------------------------------
# List saved certificates
# --------------------------------------------------

@app.route("/api/certificates", methods=["GET"])
def list_certificates():
    try:
        records = get_all_certificates()

        return jsonify({
            "success": True,
            "total": len(records),
            "certificates": records,
        })

    except Exception as error:
        app.logger.exception("Could not retrieve certificates")

        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


# --------------------------------------------------
# Verify certificate by ID
# --------------------------------------------------

@app.route("/api/verify/<certificate_id>", methods=["GET"])
def verify_certificate(certificate_id):
    record = get_certificate(certificate_id)

    if record is None:
        return jsonify({
            "success": False,
            "verified": False,
            "message": "Certificate not found",
        }), 404

    return jsonify({
        "success": True,
        "verified": True,
        "certificate": record,
    })


# --------------------------------------------------
# Download generated certificates ZIP
# --------------------------------------------------

@app.route("/api/download/<batch_id>", methods=["GET"])
def download_certificates(batch_id):
    # Only accept hexadecimal batch IDs.
    if not batch_id or any(
        character not in "0123456789abcdef"
        for character in batch_id.lower()
    ):
        return jsonify({
            "success": False,
            "message": "Invalid batch ID",
        }), 400

    zip_path = GENERATED_FOLDER / batch_id / "certificates.zip"

    if not zip_path.is_file():
        return jsonify({
            "success": False,
            "message": "Certificate file not found",
        }), 404

    return send_file(
        str(zip_path),
        as_attachment=True,
        download_name="certificates.zip",
    )


# --------------------------------------------------
# Run Flask application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
