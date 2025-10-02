from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

def generate_pdf_report(logs, filename="helmet_report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("📊 Helmet Detection Report", styles["Title"]))
    story.append(Spacer(1, 20))

    # Table header
    data = [["Timestamp", "Class", "Confidence", "Filename", "S3 URL"]]

    # Add detection logs
    for log in logs:
        timestamp, filename, class_label, confidence, s3_url = log
        data.append([
            str(timestamp),
            class_label,
            f"{confidence:.2f}",
            filename,
            s3_url
        ])

    # Create table
    table = Table(data, colWidths=[100, 80, 70, 100, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))

    story.append(table)
    doc.build(story)
    return filename
