"""
Generates synthetic DOCX and PDF test fixtures for automated testing.
"""
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import fitz
from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

def create_simple_docx_template():
    doc = docx.Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.8)
    sec.bottom_margin = Inches(0.8)
    sec.left_margin = Inches(0.8)
    sec.right_margin = Inches(0.8)

    # Header & Footer
    sec.header.paragraphs[0].text = "ACADEMIC TRANSCRIPT OFFICIAL REPORT"
    sec.footer.paragraphs[0].text = "Confidential Document - Page 1 of 1"

    # Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("OFFICIAL TRANSCRIPT OF RECORDS")
    r_title.bold = True
    r_title.font.size = Pt(16)
    r_title.font.color.rgb = RGBColor(30, 64, 175)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Placeholders
    p1 = doc.add_paragraph()
    p1.add_run("Student Name: ").bold = True
    p1.add_run("{{student_name}}")

    p2 = doc.add_paragraph()
    p2.add_run("Student ID: ").bold = True
    p2.add_run("{{student_id}}")

    p3 = doc.add_paragraph()
    p3.add_run("Degree Program: ").bold = True
    p3.add_run("{{degree}}")

    p4 = doc.add_paragraph()
    p4.add_run("Cumulative GPA: ").bold = True
    p4.add_run("{{gpa}}")

    p5 = doc.add_paragraph()
    p5.add_run("Graduation Date: ").bold = True
    p5.add_run("{{graduation_date}}")

    path = FIXTURES_DIR / "simple_template.docx"
    doc.save(str(path))
    return path

def create_complex_docx_template():
    doc = docx.Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.7)
    sec.bottom_margin = Inches(0.7)

    p_title = doc.add_paragraph()
    p_title.add_run("SEMESTER PERFORMANCE REPORT").bold = True
    p_title.runs[0].font.size = Pt(14)

    # Table with placeholders
    table = doc.add_table(rows=4, cols=3)
    headers = ["Course Code", "Course Title", "Grade"]
    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.paragraphs[0].runs[0].bold = True

    sample_rows = [
        ["CS101", "Introduction to Computing", "{{cs101_grade}}"],
        ["CS201", "Data Structures & Algorithms", "{{cs201_grade}}"],
        ["MATH301", "Linear Algebra", "{{math301_grade}}"]
    ]
    for r_idx, row in enumerate(sample_rows):
        for c_idx, val in enumerate(row):
            table.cell(r_idx + 1, c_idx).text = val

    path = FIXTURES_DIR / "complex_template.docx"
    doc.save(str(path))
    return path

def create_digital_reference_pdf():
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842) # A4
    text = (
        "UNIVERSITY ACADEMIC RECORDS ARCHIVE\n\n"
        "Student Information Sheet\n"
        "Student Name: Alexander Wright\n"
        "Student ID: STU-98421\n"
        "Degree Program: Bachelor of Computer Science\n"
        "Cumulative GPA: 3.88\n"
        "Graduation Date: June 15, 2024\n"
        "Dean Honors: First Class with Distinction\n\n"
        "Grade Breakdown:\n"
        "CS101: A\n"
        "CS201: A-\n"
        "MATH301: B+\n"
    )
    page.insert_text(fitz.Point(50, 60), text, fontsize=11)
    path = FIXTURES_DIR / "digital_reference.pdf"
    pdf.save(str(path))
    pdf.close()
    return path

def create_conflicting_reference_pdf():
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    text = (
        "SECONDARY TRANSCRIPT RECORD\n\n"
        "Student Name: Alex Wright\n"
        "Cumulative GPA: 3.75\n"
        "Graduation Date: May 20, 2024\n"
    )
    page.insert_text(fitz.Point(50, 60), text, fontsize=11)
    path = FIXTURES_DIR / "conflicting_reference.pdf"
    pdf.save(str(path))
    pdf.close()
    return path

def create_scanned_reference_pdf():
    # Render an image with crisp text and put it into PDF to simulate a scanned document
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
    font_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    
    d.text((40, 50), "SCANNED CERTIFICATE OF ENROLLMENT", fill=(0, 0, 0), font=font_large)
    d.text((40, 120), "Student Name: Alexander Wright", fill=(0, 0, 0), font=font_body)
    d.text((40, 160), "Student ID: STU-98421", fill=(0, 0, 0), font=font_body)
    d.text((40, 200), "Degree Program: Bachelor of Computer Science", fill=(0, 0, 0), font=font_body)
    d.text((40, 240), "Date of Issue: October 12, 2023", fill=(0, 0, 0), font=font_body)

    img_path = FIXTURES_DIR / "temp_scanned.png"
    img.save(str(img_path))

    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    page.insert_image(page.rect, filename=str(img_path))
    path = FIXTURES_DIR / "scanned_reference.pdf"
    pdf.save(str(path))
    pdf.close()
    img_path.unlink()
    return path

def create_pdf_template():
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    text = (
        "OFFICIAL CERTIFICATE OF COMPLETION\n\n"
        "This is to certify that [Student Name] has successfully fulfilled\n"
        "all academic requirements for the degree of [Degree Program]\n"
        "with a cumulative GPA of [GPA].\n\n"
        "Conferred on: [Graduation Date]\n"
    )
    page.insert_text(fitz.Point(50, 80), text, fontsize=12)
    path = FIXTURES_DIR / "sample_template.pdf"
    pdf.save(str(path))
    pdf.close()
    return path

if __name__ == "__main__":
    create_simple_docx_template()
    create_complex_docx_template()
    create_digital_reference_pdf()
    create_conflicting_reference_pdf()
    create_scanned_reference_pdf()
    create_pdf_template()
    print("Fixtures created successfully.")
