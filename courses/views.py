import os
import io
import logging
import zipfile
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from django.core.files.storage import default_storage
from django.db.models import Q
from .models import Course, SectionNote, LectureFinalNote
from category.models import CourseCategory
from .ai_helpers import extract_text_from_image, structure_text_with_gemini
from .utils import create_pdf_from_markdown_bytes, generate_final_pdf_from_notes
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import requests
from django.core.files.base import ContentFile
from image_enhancer.utils.document_enhancer import enhance_document

logger = logging.getLogger(__name__)


def course(request, category_slug=None):
    """
    List courses or list courses in a category.
    """
    category = None
    if category_slug:
        category = get_object_or_404(CourseCategory, slug=category_slug)
        courses = Course.objects.filter(category=category)
        paginator = Paginator(courses, 9)
        page = request.GET.get('page')
        paged_courses= paginator.get_page(page)
    else:
        courses = Course.objects.all()
        paginator = Paginator(courses, 9)
        page = request.GET.get('page')
        paged_courses= paginator.get_page(page)
    return render(request, "course/course.html", {"courses": paged_courses, "category": category})

    
def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            courses = Course.objects.filter(Q(faculty_initial__icontains=keyword) | Q(course_initial__icontains=keyword))
            course_count = courses.count()
    context = {
        'courses': courses,
        'course_count': course_count,
    }

    return render(request, "course/course.html",context)

@login_required(login_url="login")
def course_detail(request, category_slug, course_slug, section, lecture):
    category = get_object_or_404(CourseCategory, slug=category_slug)
    course = get_object_or_404(Course, category=category, slug=course_slug, section=section)
    generated_notes = None

    if request.method == "POST":
        images = request.FILES.getlist("images")
        if not images:
            return HttpResponseBadRequest("No images uploaded.")

        all_text = []

        for img_file in images:
            # Save image directly to Cloudinary via SectionNote
            sn = SectionNote.objects.create(
                user=request.user,
                course=course,
                lecture=lecture,
                image=img_file
            )

            try:
                # Download image from Cloudinary to memory for OCR
                resp = requests.get(sn.image.url)
                tmp_file = ContentFile(resp.content)

                extracted = extract_text_from_image(tmp_file)  # must accept file-like
            except Exception as e:
                logger.exception("OCR failed for %s: %s", sn.image.url, e)
                extracted = "(Error extracting text)"

            sn.extracted_text = extracted
            sn.save()
            all_text.append(extracted)

        combined = "\n\n".join(all_text)

        try:
            generated_notes = structure_text_with_gemini(combined)
        except Exception as e:
            logger.exception("AI notes generation failed: %s", e)
            generated_notes = combined

    context = {
        "single_course": course,
        "category": category,
        "lecture": lecture,
        "notes": generated_notes,
    }
    return render(request, "course/course_detail.html", context)


@login_required(login_url="login")
def course_detail_per_section(request, category_slug, course_slug, section, lecture):
    category = get_object_or_404(CourseCategory, slug=category_slug)
    course = get_object_or_404(Course, slug=course_slug, category=category, section=section)

    # Fetch notes and group by user
    all_notes = SectionNote.objects.filter(course=course, lecture=lecture).select_related("user").order_by("-uploaded_at")
    lecture_notes_grouped = defaultdict(list)
    for note in all_notes:
        lecture_notes_grouped[note.user].append(note)
    lecture_notes_grouped_list = list(lecture_notes_grouped.items())

    # Get final AI notes if exist
    final_note_obj = LectureFinalNote.objects.filter(course=course, lecture=lecture).first()
    final_notes = final_note_obj.notes if final_note_obj else None

    # Handle uploaded images
    if request.method == "POST":
        images = request.FILES.getlist("images")
        if not images:
            return HttpResponseBadRequest("No images uploaded.")

        all_text_parts = []

        for img_file in images:
            # Save SectionNote without local file path
            sn = SectionNote.objects.create(
                user=request.user,
                course=course,
                lecture=lecture,
                image=img_file  # Cloudinary handles storage
            )

            # Download image in-memory for OCR (works with Cloudinary URL)
            img_url = sn.image.url
            try:
                resp = requests.get(img_url)
                image_file = io.BytesIO(resp.content)
                extracted = extract_text_from_image(image_file)
            except Exception as e:
                extracted = "(Error extracting text)"

            sn.extracted_text = extracted
            sn.save()
            all_text_parts.append(extracted)

        combined_text = "\n\n".join(all_text_parts)

        # Generate AI notes
        try:
            generated_notes = structure_text_with_gemini(combined_text)
        except Exception:
            generated_notes = combined_text

        # Save/update LectureFinalNote
        if final_note_obj:
            final_note_obj.notes = generated_notes
            final_note_obj.save()
        else:
            LectureFinalNote.objects.create(course=course, lecture=lecture, notes=generated_notes)

        return redirect(
            "course_detail_per_section",
            category_slug=category_slug,
            course_slug=course_slug,
            section=section,
            lecture=lecture
        )

    context = {
        "course": course,
        "category": category,
        "section": section,
        "lecture": lecture,
        "lecture_notes_grouped": lecture_notes_grouped_list,
        "final_notes": final_notes,
        "final_note_obj": final_note_obj,
    }
    return render(request, "course/lecture_detail.html", context)

@login_required(login_url="login")
def download_lecture_notes_pdf(request, category_slug, course_slug, section, lecture):
    """
    Combine all SectionNote.extracted_text from all users for a lecture into a single PDF.
    Optionally saves it to LectureFinalNote.pdf_file for caching.
    """
    # 1️⃣ Get the course safely
    course = Course.objects.filter(
        slug=course_slug, category__slug=category_slug, section=section
    ).first()
    if not course:
        return HttpResponse("Course not found.", status=404)

    # 2️⃣ Get all SectionNote objects for this lecture
    notes_qs = SectionNote.objects.filter(course=course, lecture=lecture)
    if not notes_qs.exists():
        return HttpResponse("No notes uploaded for this lecture.", status=404)

    # 3️⃣ Combine all extracted_text
    combined_text = ""
    for i, note in enumerate(notes_qs, start=1):
        user_name = getattr(note.user, "username", "User")
        combined_text += f"## Note {i} by {user_name}\n\n"
        combined_text += (note.extracted_text or "(No text available)") + "\n\n"

    # 4️⃣ Generate PDF
    try:
        pdf_buffer = create_pdf_from_markdown_bytes(combined_text)
        pdf_bytes = pdf_buffer.getvalue()
    except Exception as e:
        logger.exception("Failed to generate PDF: %s", e)
        return HttpResponse("Failed to generate PDF.", status=500)

    # 5️⃣ Save to LectureFinalNote for caching (optional)
    lecture_final, created = LectureFinalNote.objects.get_or_create(
        course=course,
        lecture=lecture,
        defaults={"notes": combined_text, "is_generated": True, "next_pdf_time": timezone.now()}
    )

    if not created:
        lecture_final.notes = combined_text
        lecture_final.is_generated = True
        lecture_final.next_pdf_time = timezone.now()
        lecture_final.pdf_file.save(
            f"{course.slug}_lecture_{lecture}_combined.pdf",
            io.BytesIO(pdf_bytes),
            save=True
        )
    else:
        lecture_final.pdf_file.save(
            f"{course.slug}_lecture_{lecture}_combined.pdf",
            io.BytesIO(pdf_bytes),
            save=True
        )

    # 6️⃣ Return PDF to user
    filename = f"{course.slug}_lecture_{lecture}_all_users.pdf"
    return FileResponse(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf"
    )

# -----------------------------
# Download User Images (ZIP)
# -----------------------------
@login_required(login_url="login")
def download_user_images(request, user_id, category_slug, course_slug, section, lecture):
    course = get_object_or_404(Course, slug=course_slug, category__slug=category_slug, section=section)
    notes = SectionNote.objects.filter(user_id=user_id, course=course, lecture=lecture)

    if not notes.exists():
        return HttpResponse("No images found for this user.", status=404)

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zip_file:
        for note in notes:
            # Download image from Cloudinary
            resp = requests.get(note.image.url)
            tmp_file = io.BytesIO(resp.content)

            # Optional: enhance image in-memory
            try:
                # Save to temporary path to pass into your OpenCV enhancer
                tmp_path = f"/tmp/{note.image.name}"
                with open(tmp_path, "wb") as f:
                    f.write(tmp_file.getvalue())
                enhanced_path = tmp_path.replace(".","_enhanced.")
                enhance_document(tmp_path, enhanced_path)

                # Add enhanced image to ZIP
                with open(enhanced_path, "rb") as f:
                    zip_file.writestr(f"enhanced_{note.image.name}", f.read())
            except Exception:
                # Fallback: use original image
                zip_file.writestr(note.image.name, tmp_file.getvalue())

    buffer.seek(0)
    filename = f"user_{user_id}_lecture_{lecture}_images.zip"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type="application/zip")

@login_required(login_url="login")
def enhance_view(request):
    """
    API endpoint to enhance uploaded images.
    - Accepts multiple image files.
    - Returns single enhanced image or a ZIP for multiple images.
    Fully compatible with Cloudinary uploads.
    """
    if request.method != "POST":
        return render(request, "course/lecture_detail.html")

    files = request.FILES.getlist("images")
    if not files:
        return HttpResponseBadRequest("No images uploaded.")

    output_files = []

    for file in files:
        # Read uploaded file into BytesIO
        img_bytes = io.BytesIO(file.read())

        try:
            # Pass BytesIO to enhance_document
            enhanced_bytes = enhance_document(img_bytes)  # modify enhance_document to accept BytesIO
        except Exception as e:
            logger.exception("Enhancement failed for %s: %s", file.name, e)
            enhanced_bytes = img_bytes  # fallback to original

        output_files.append((file.name, enhanced_bytes))

    # If only one file, return directly
    if len(output_files) == 1:
        filename, content = output_files[0]
        content.seek(0)
        return FileResponse(content, filename=f"enhanced_{filename}", content_type="image/png")

    # Multiple files -> create in-memory ZIP
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w") as zf:
        for filename, content in output_files:
            content.seek(0)
            zf.writestr(f"enhanced_{filename}", content.read())
    mem_zip.seek(0)
    return FileResponse(mem_zip, as_attachment=True, filename="enhanced_images.zip", content_type="application/zip")