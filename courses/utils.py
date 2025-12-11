import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from .models import SectionNote, LectureFinalNote


# -----------------------------
# Markdown → PDF GENERATOR
# -----------------------------
def create_pdf_from_markdown_bytes(md_text: str) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    
    styles = getSampleStyleSheet()
    
    header = ParagraphStyle(
        name="Header",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=12,
        spaceBefore=12,
    )
    
    subheader = ParagraphStyle(
        name="SubHeader",
        parent=styles["Heading2"],
        fontSize=16,
        spaceAfter=10,
        spaceBefore=10,
    )
    
    body = ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontSize=12,
        leading=16,
    )
    
    bullet = ParagraphStyle(
        name="Bullet",
        parent=styles["BodyText"],
        bulletIndent=20,
        leftIndent=20,
        spaceAfter=5,
    )
    
    elements = []
    
    for line in md_text.split("\n"):
        line = line.strip()
    
        if not line:
            elements.append(Spacer(1, 10))
            continue
    
        # Headers
        if line.startswith("# "):
            elements.append(Paragraph(line[2:], header))
            continue
    
        if line.startswith("### "):
            elements.append(Paragraph(line[3:], subheader))
            continue
    
        # Bullet points
        if line.startswith("* "):
            elements.append(Paragraph("• " + line[2:], bullet))
            continue
    
        # Normal paragraph
        elements.append(Paragraph(line, body))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


# -----------------------------
# PDF CREATOR FOR LECTURE FINAL NOTES
# -----------------------------
def generate_final_pdf_from_notes(lecture_final_obj: LectureFinalNote):
    """
    Combine all SectionNote OCR text → structure with Gemini → export PDF.
    Attach generated PDF to LectureFinalNote.pdf_file field.
    """

    from .ai_helpers import structure_text_with_gemini  # safe import

    course = lecture_final_obj.course
    lecture_no = lecture_final_obj.lecture

    notes_qs = SectionNote.objects.filter(
        course=course, lecture=lecture_no
    ).order_by("uploaded_at")

    combined_text = ""

    for note in notes_qs:
        if note.extracted_text:
            combined_text += note.extracted_text + "\n\n"
        else:
            combined_text += "(No extracted text)\n\n"

    # Use existing notes if user edited them previously
    raw_input = lecture_final_obj.notes or combined_text

    # Run Gemini if available
    try:
        markdown = structure_text_with_gemini(raw_input)
    except Exception:
        markdown = raw_input

    # Convert markdown → PDF
    pdf_buffer = create_pdf_from_markdown_bytes(markdown)

    # Save to model
    filename = (
        f"final_pdfs/{course.slug}_lecture_{lecture_no}_"
        f"{int(timezone.now().timestamp())}.pdf"
    )

    content = ContentFile(pdf_buffer.read())
    lecture_final_obj.pdf_file.save(filename, content)

    lecture_final_obj.notes = markdown
    lecture_final_obj.save()

    return lecture_final_obj.pdf_file.path
