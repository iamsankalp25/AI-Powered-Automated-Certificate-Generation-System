
import os
import zipfile

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth


# --------------------------------------------------
# Certificate template settings
# --------------------------------------------------

TEMPLATES = {
    "classic": {
        "background": "#FFFCF3",
        "primary": "#B8860B",
        "secondary": "#E6C86E",
        "title": "#292524",
        "text": "#57534E",
        "accent": "#92700C",
    },
    "modern": {
        "background": "#F7F5FF",
        "primary": "#6D28D9",
        "secondary": "#C4B5FD",
        "title": "#2E1065",
        "text": "#5B556B",
        "accent": "#7C3AED",
    },
    "elegant": {
        "background": "#F3FAF5",
        "primary": "#166534",
        "secondary": "#86C79A",
        "title": "#163B28",
        "text": "#4B6353",
        "accent": "#15803D",
    },
}


def safe_filename(name):
    """Convert participant name into a safe PDF filename."""
    name = str(name).strip()

    invalid_chars = '<>:"/\\|?*'

    for char in invalid_chars:
        name = name.replace(char, "")

    return name if name else "Certificate"


def draw_centered_text(
    c, text, y, font="Helvetica", size=16, color="#222222"
):
    """Draw text centered on the page."""
    width, _ = A4
    text = str(text)

    c.setFont(font, size)
    c.setFillColor(HexColor(color))

    text_width = stringWidth(text, font, size)
    c.drawString((width - text_width) / 2, y, text)


def draw_wrapped_centered_text(
    c, text, y, max_width, font, size, color, leading=None
):
    """Wrap longer text into centered lines."""
    text = str(text)
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()

        if stringWidth(test_line, font, size) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    if not lines:
        lines = [""]

    line_height = leading or size * 1.4

    for line in lines:
        draw_centered_text(c, line, y, font, size, color)
        y -= line_height

    return y


def draw_certificate_design(c, width, height, template):
    """Draw the selected certificate's background and borders."""
    colors = TEMPLATES[template]

    # Background
    c.setFillColor(HexColor(colors["background"]))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Main border
    c.setStrokeColor(HexColor(colors["primary"]))
    c.setLineWidth(4)

    c.rect(
        35, 35,
        width - 70, height - 70,
        fill=0, stroke=1
    )

    # Inner border
    c.setStrokeColor(HexColor(colors["secondary"]))
    c.setLineWidth(1.3)

    c.rect(
        49, 49,
        width - 98, height - 98,
        fill=0, stroke=1
    )

    if template == "classic":
        # Traditional gold corner decorations
        c.setStrokeColor(HexColor(colors["primary"]))
        c.setLineWidth(2)

        for x, y, dx, dy in [
            (58, 58, 1, 1),
            (width - 58, 58, -1, 1),
            (58, height - 58, 1, -1),
            (width - 58, height - 58, -1, -1),
        ]:
            c.line(x, y, x + dx * 22, y)
            c.line(x, y, x, y + dy * 22)

    elif template == "modern":
        # Contemporary purple top and bottom accent bars
        c.setFillColor(HexColor(colors["primary"]))
        c.rect(50, height - 62, width - 100, 5, fill=1, stroke=0)
        c.rect(50, 57, width - 100, 5, fill=1, stroke=0)

        c.setFillColor(HexColor(colors["secondary"]))
        c.circle(67, height - 78, 5, fill=1, stroke=0)
        c.circle(width - 67, height - 78, 5, fill=1, stroke=0)

    elif template == "elegant":
        # Green side accents
        c.setFillColor(HexColor(colors["secondary"]))
        c.rect(50, 80, 5, height - 160, fill=1, stroke=0)
        c.rect(width - 55, 80, 5, height - 160, fill=1, stroke=0)

        c.setStrokeColor(HexColor(colors["primary"]))
        c.setLineWidth(1.5)
        c.line(150, height - 83, width - 150, height - 83)
        c.line(150, 83, width - 150, 83)


def generate_certificate(record, output_folder, template="classic"):
    """Generate one certificate using the selected design."""
    os.makedirs(output_folder, exist_ok=True)

    if template not in TEMPLATES:
        template = "classic"

    colors = TEMPLATES[template]

    name = str(record["Name"]).strip()
    event = str(record["Event"]).strip()
    organization = str(record["Organization"]).strip()
    date = str(record["Date"]).strip()
    achievement = str(record["Achievement"]).strip()
    certificate_id = str(record.get("certificate_id", "N/A"))

    filename = f"{safe_filename(name)}.pdf"
    output_path = os.path.join(output_folder, filename)

    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    # Selected template background and decorations
    draw_certificate_design(c, width, height, template)

    # Organization
    draw_wrapped_centered_text(
        c,
        organization,
        height - 125,
        width - 150,
        "Helvetica-Bold",
        18,
        colors["primary"],
        23,
    )

    # Certificate title
    draw_centered_text(
        c,
        "CERTIFICATE",
        height - 190,
        "Helvetica-Bold",
        31,
        colors["title"],
    )

    draw_centered_text(
        c,
        "OF ACHIEVEMENT",
        height - 220,
        "Helvetica-Bold",
        14,
        colors["accent"],
    )

    # Decorative divider
    divider_y = height - 245
    c.setStrokeColor(HexColor(colors["secondary"]))
    c.setLineWidth(1.5)
    c.line(175, divider_y, width - 175, divider_y)

    # Presented to
    draw_centered_text(
        c,
        "This certificate is proudly presented to",
        height - 285,
        "Helvetica",
        13,
        colors["text"],
    )

    # Participant name
    name_size = 28

    while (
        stringWidth(name, "Helvetica-Bold", name_size) > width - 130
        and name_size > 16
    ):
        name_size -= 1

    draw_centered_text(
        c,
        name,
        height - 340,
        "Helvetica-Bold",
        name_size,
        colors["primary"],
    )

    # Name underline
    c.setStrokeColor(HexColor(colors["secondary"]))
    c.setLineWidth(1.5)
    c.line(130, height - 355, width - 130, height - 355)

    # Achievement
    draw_wrapped_centered_text(
        c,
        achievement,
        height - 400,
        width - 120,
        "Helvetica-Bold",
        14,
        colors["title"],
        19,
    )

    # Event
    draw_wrapped_centered_text(
        c,
        f"for participating in {event}",
        height - 450,
        width - 120,
        "Helvetica",
        12,
        colors["text"],
        17,
    )

    # Date
    draw_centered_text(
        c,
        f"Date: {date}",
        height - 505,
        "Helvetica",
        12,
        colors["text"],
    )

    # Certificate ID
    draw_centered_text(
        c,
        f"Certificate ID: {certificate_id}",
        height - 532,
        "Helvetica-Bold",
        10,
        colors["primary"],
    )

    # Signature lines
    c.setStrokeColor(HexColor(colors["primary"]))
    c.setLineWidth(1)

    c.line(85, 135, 245, 135)
    c.line(width - 245, 135, width - 85, 135)

    draw_centered_text(
        c,
        "Authorized Signature",
        115,
        "Helvetica",
        10,
        colors["text"],
    )

    right_text = "Certificate Authority"
    right_width = stringWidth(right_text, "Helvetica", 10)

    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor(colors["text"]))
    c.drawString(
        width - 165 - right_width / 2,
        115,
        right_text,
    )

    # Footer
    draw_centered_text(
        c,
        "Generated by CertiAI",
        75,
        "Helvetica",
        9,
        colors["text"],
    )

    c.save()
    return output_path


def generate_bulk_certificates(
    records, output_folder, template="classic"
):
    """Generate certificates using one selected template and ZIP them."""
    os.makedirs(output_folder, exist_ok=True)

    if template not in TEMPLATES:
        template = "classic"

    generated_files = []

    for record in records:
        pdf_path = generate_certificate(
            record,
            output_folder,
            template=template,
        )
        generated_files.append(pdf_path)

    zip_path = os.path.join(output_folder, "certificates.zip")

    with zipfile.ZipFile(
        zip_path, "w", zipfile.ZIP_DEFLATED
    ) as zip_file:
        for pdf_path in generated_files:
            zip_file.write(
                pdf_path,
                os.path.basename(pdf_path),
            )

    return zip_path, generated_files
