from django.shortcuts import render, get_object_or_404,redirect
from .models import Course, SectionNote,LectureFinalNote
from category.models import CourseCategory
from PIL import Image
import google.generativeai as genai
import os
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.contrib.auth.decorators import login_required

from django.http import FileResponse
from collections import defaultdict
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))




def extract_text_from_image(image_path):
    ocr_model = genai.GenerativeModel("gemini-2.5-flash")
    img = Image.open(image_path)
    prompt = "Extract handwritten text accurately from this image."

    try:
        response = ocr_model.generate_content([prompt, img])
        return response.text.strip() if response.text else "(No text found)"
    except:
        return "(Error extracting text)"
    
def course(request, category_slug=None):
    category = None
    if category_slug:
        category = get_object_or_404(CourseCategory, slug=category_slug)
        courses = Course.objects.filter(category=category)
    else:
        courses = Course.objects.all()

    return render(request, "course/course.html", {"courses": courses, "category": category})


def structure_text_with_gemini(all_text):
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
    "You are an expert in cleaning messy OCR text. The input contains handwritten OCR output "
    "with mistakes, missing symbols, spacing issues, inconsistent formatting, and broken structure.\n\n"

    "🎯 YOUR TASK:\n"
    "Reconstruct the text into **clean, accurate, well-structured Markdown** WITHOUT changing the meaning.\n"
    "You must FIX errors, but NEVER summarize or remove information.\n\n"

    "📌 STRICT RULES:\n"
    "1. Convert everything into clean Markdown structure.\n"
    "2. Use:\n"
    "   - `#` for main headings\n"
    "   - `##` for subheadings\n"
    "   - `-` for bullet points (only hyphen, never *, ** or *** )\n"
    "   - ` ``` ` fenced code blocks for any code-like text\n"
    "3. Preserve ALL content. Do NOT shorten, compress, or remove technical meaning.\n"
    "4. Correct OCR errors ONLY when obvious (e.g., wrong variable name, incomplete word). "
    "After correcting, add a note below the line in parentheses explaining the correction in 1 short sentence.\n"
    "5. When a new topic begins, create a proper heading.\n"
    "6. Fix indentation, spacing, line breaks, and list structure.\n"
    "7. Keep examples exactly as given.\n"
    "8. DO NOT rewrite explanations unless the OCR text is incomplete — then repair the sentence clearly.\n"
    "9. Keep the output purely Markdown. No emojis.\n\n"

    "📌 INPUT (messy OCR text):\n"
    f"{all_text}\n\n"
    "📌 OUTPUT (fully cleaned Markdown only):"
)

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else all_text
    except:
        return all_text


@login_required(login_url="login")
def course_detail(request, category_slug, course_slug, section):
    category = get_object_or_404(CourseCategory, slug=category_slug)
    single_course = get_object_or_404(Course, category=category, slug=course_slug, section=section)

    generated_notes = None

    if request.method == "POST":
        images = request.FILES.getlist("images")
        os.makedirs("media", exist_ok=True)

        all_text = ""
        for img_file in images:
            save_path = os.path.join("media", img_file.name)
            with open(save_path, "wb+") as f:
                for chunk in img_file.chunks():
                    f.write(chunk)

            text = extract_text_from_image(save_path)
            all_text += text + "\n\n"

        # 🧠 Generate summarized notes using Gemini
        generated_notes = structure_text_with_gemini(all_text)

    context = {
        "single_course": single_course,
        "category": category,
        "notes": generated_notes,
    }

    return render(request, "course/course_detail.html", context)

def create_pdf_from_markdown(md_text):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Preformatted
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # ---------- STYLES ----------
    h1 = ParagraphStyle(
        "Heading1",
        parent=styles["Heading1"],
        fontSize=22,
        spaceAfter=12,
        spaceBefore=12,
    )
    h2 = ParagraphStyle(
        "Heading2",
        parent=styles["Heading2"],
        fontSize=18,
        textColor="#333333",
        spaceAfter=8,
        spaceBefore=10
    )
    h3 = ParagraphStyle(
        "Heading3",
        parent=styles["Heading3"],
        fontSize=15,
        textColor="#555555",
        spaceAfter=6,
        spaceBefore=6
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=12,
        leading=18,
        spaceAfter=6
    )
    code_style = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=10,
        leading=14,
        backColor="#f5f5f5",
        leftIndent=10,
        rightIndent=10,
        spaceBefore=6,
        spaceAfter=6,
    )

    elements = []
    lines = md_text.split("\n")

    in_code_block = False
    code_buffer = []

    for line in lines:
        line = line.rstrip()

        # ---------- CODE BLOCKS ----------
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_buffer = []
            else:
                in_code_block = False
                code_text = "\n".join(code_buffer)
                elements.append(Preformatted(code_text, code_style))
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # ---------- HEADINGS ----------
        if line.startswith("# "):
            elements.append(Paragraph(line[2:], h1))
            continue
        if line.startswith("## "):
            elements.append(Paragraph(line[3:], h2))
            continue
        if line.startswith("### "):
            elements.append(Paragraph(line[4:], h3))
            continue

        # ---------- BULLET POINTS ----------
        if line.startswith(("• ", "- ", "* ")):
            bullet_list = ListFlowable(
                [ListItem(Paragraph(line[2:], body), bulletFontSize=10, leftIndent=20)],
                bulletType="bullet",
                start=""
            )
            elements.append(bullet_list)
            continue

        # ---------- NORMAL TEXT ----------
        if line.strip():
            elements.append(Paragraph(line, body))
        else:
            elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return buffer

@login_required(login_url="login")
def download_lecture_notes_pdf(request, category_slug, course_slug, section, lecture):

    course = get_object_or_404(Course, slug=course_slug)
    final_note_obj = get_object_or_404(LectureFinalNote, course=course, lecture=lecture)

    md_text = final_note_obj.notes

    pdf_buffer = create_pdf_from_markdown(md_text)

    filename = f"{course_slug}_lecture_{lecture}_notes.pdf"

    return HttpResponse(
        pdf_buffer,
        content_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@login_required(login_url="login")
def course_detail_per_section(request, category_slug, course_slug, section, lecture):
    
    category = get_object_or_404(CourseCategory, slug=category_slug)
    course = get_object_or_404(
        Course,
        slug=course_slug,
        category=category,
        section=section
    )
    



    # --- Fetch Section Note images for THIS lecture only ---
    all_notes = (
        SectionNote.objects
        .filter(course=course, lecture=lecture)
        .select_related("user")
        .order_by("-uploaded_at")
    )

    # --- Group notes by user ---
    lecture_notes_grouped = defaultdict(list)
    for note in all_notes:
        lecture_notes_grouped[note.user].append(note)

    lecture_notes_grouped_list = list(lecture_notes_grouped.items())

    # --- Get final AI notes if exist ---
    final_note_obj = LectureFinalNote.objects.filter(
        course=course,
        lecture=lecture
    ).first()

    final_notes = final_note_obj.notes if final_note_obj else None

    # --- Handle Upload POST ---
    if request.method == "POST":
        images = request.FILES.getlist("images")

        all_text = ""

        for img in images:
            new_note = SectionNote.objects.create(
                user=request.user,
                course=course,
                lecture=lecture,
                image=img
            )

            extracted = extract_text_from_image(new_note.image.path)
            new_note.extracted_text = extracted
            new_note.save()

            all_text += extracted + "\n\n"

        # Generate AI Notes using Gemini
        generated_notes = structure_text_with_gemini(all_text)

        if final_note_obj:
            final_note_obj.notes = generated_notes
            final_note_obj.save()
        else:
            LectureFinalNote.objects.create(
                course=course,
                lecture=lecture,
                notes=generated_notes
            )

        return redirect(
            "course_detail_per_section",
            category_slug=category_slug,
            course_slug=course_slug,
            section=section,
            lecture=lecture
        )

    # --- Render Template ---
    context = {
        "course": course,
        "category": category,
        "section": section,
        "lecture": lecture,
        "lecture_notes_grouped": lecture_notes_grouped_list,
        "final_notes": final_notes,
    }

    return render(request, "course/lecture_detail.html", context)


import zipfile
import io



@login_required(login_url="login")
def download_user_images(request, user_id, category_slug, course_slug, section, lecture):

    course = get_object_or_404(
        Course,
        slug=course_slug,
        category__slug=category_slug,
        section=section
    )

    notes = SectionNote.objects.filter(
        user_id=user_id,
        course=course,
        lecture=lecture
    )

    if not notes.exists():
        return HttpResponse("No images found for this user.", status=404)

    buffer = io.BytesIO()

    from image_enhancer.utils.document_enhancer import enhance_document

    with zipfile.ZipFile(buffer, "w") as zip_file:
        for note in notes:
            original_path = note.image.path

            # enhanced file path
            enhanced_name = "enhanced_" + os.path.basename(original_path)
            enhanced_path = os.path.join(settings.MEDIA_ROOT, "outputs", enhanced_name)
            os.makedirs(os.path.dirname(enhanced_path), exist_ok=True)

            # enhance image
            final_path = enhance_document(original_path, enhanced_path)

            # add enhanced image to ZIP
            zip_file.write(final_path, arcname=enhanced_name)

    buffer.seek(0)

    filename = f"user_{user_id}_lecture_{lecture}_enhanced_images.zip"

    response = HttpResponse(buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

'''
def download_user_images(request, user_id, category_slug, course_slug, section, lecture):

    # Get the course first
    course = get_object_or_404(
        Course,
        slug=course_slug,
        category__slug=category_slug,
        section=section
    )

    # Now fetch all notes for this course + lecture + user
    notes = SectionNote.objects.filter(
        user_id=user_id,
        course=course,
        lecture=lecture
    )

    if not notes.exists():
        return HttpResponse("No images found for this user.", status=404)

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zip_file:
        for note in notes:
            zip_file.write(note.image.path, arcname=os.path.basename(note.image.name))

    buffer.seek(0)

    filename = f"user_{user_id}_lecture_{lecture}_images.zip"

    response = HttpResponse(buffer, content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

'''

from django.http import HttpResponse, FileResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.conf import settings
import os
from zipfile import ZipFile
from image_enhancer.utils.document_enhancer import enhance_document
def enhance_view(request):
    if request.method == "POST":
        files = request.FILES.getlist("images")

        if not files:
            return HttpResponseBadRequest("No images uploaded.")

        output_files = []

        for file in files:
            # Save input
            input_path = default_storage.save("uploads/" + file.name, file)
            input_path = os.path.join(settings.MEDIA_ROOT, input_path)

            # Prepare output
            output_name = "enhanced_" + file.name
            output_path = os.path.join(settings.MEDIA_ROOT, "outputs", output_name)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Enhance
            final_path = enhance_document(input_path, output_path)
            output_files.append(final_path)

        # 🔥 If only 1 image was uploaded → return enhanced image directly
        if len(output_files) == 1:
            return FileResponse(open(output_files[0], 'rb'), content_type='image/png')

        # 🔥 If multiple → create a ZIP file and return it
        zip_path = os.path.join(settings.MEDIA_ROOT, "outputs", "enhanced_images.zip")
        with ZipFile(zip_path, "w") as zipf:
            for p in output_files:
                zipf.write(p, os.path.basename(p))

        return FileResponse(open(zip_path, 'rb'), content_type="application/zip")

    return render(request, "course/lecture_detail.html")
