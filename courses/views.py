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
def course_detail(request, category_slug, course_slug, section):
    """
    Simple course detail view that accepts image uploads (single view example).
    This view returns generated notes (not saved to LectureFinalNote here).
    Use course_detail_per_section for per-lecture flows.
    """
    category = get_object_or_404(CourseCategory, slug=category_slug)
    single_course = get_object_or_404(Course, category=category, slug=course_slug, section=section)
    generated_notes = None

    if request.method == "POST":
        images = request.FILES.getlist("images")
        if not images:
            return HttpResponseBadRequest("No images uploaded.")

        # ensure media temp dir exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        all_text = []
        for img_file in images:
            # Save to a temporary path via default_storage to avoid direct FS assumptions
            tmp_name = default_storage.save(f"temp_uploads/{img_file.name}", img_file)
            tmp_path = os.path.join(settings.MEDIA_ROOT, tmp_name)

            try:
                text = extract_text_from_image(tmp_path)
            except Exception as e:
                logger.exception("OCR failed for %s: %s", tmp_path, e)
                text = "(Error extracting text)"
            all_text.append(text)

            # optionally remove tmp file
            try:
                default_storage.delete(tmp_name)
            except Exception:
                pass

        combined = "\n\n".join(all_text)
        try:
            generated_notes = structure_text_with_gemini(combined)
        except Exception as e:
            logger.exception("structure_text_with_gemini failed: %s", e)
            generated_notes = combined

    context = {
        "single_course": single_course,
        "category": category,
        "notes": generated_notes,
    }
    return render(request, "course/course_detail.html", context)


@login_required(login_url="login")
def course_detail_per_section(request, category_slug, course_slug, section, lecture):
    """
    Main per-lecture page:
    - Lists uploaded images grouped by user
    - Accepts uploads, runs OCR + Gemini, creates/updates LectureFinalNote
    """
    category = get_object_or_404(CourseCategory, slug=category_slug)
    course = get_object_or_404(Course, slug=course_slug, category=category, section=section)

    # Fetch notes for the specific lecture
    all_notes = (
        SectionNote.objects.filter(course=course, lecture=lecture)
        .select_related("user")
        .order_by("-uploaded_at")
    )

    # Group notes by user
    lecture_notes_grouped = defaultdict(list)
    for note in all_notes:
        lecture_notes_grouped[note.user].append(note)
    lecture_notes_grouped_list = list(lecture_notes_grouped.items())

    # Get the final AI notes if exist
    final_note_obj = LectureFinalNote.objects.filter(course=course, lecture=lecture).first()
    final_notes = final_note_obj.notes if final_note_obj else None

    if request.method == "POST":
        images = request.FILES.getlist("images")
        if not images:
            return HttpResponseBadRequest("No images uploaded.")

        all_text_parts = []

        # Save SectionNote objects and extract OCR immediately
        for img in images:
            sn = SectionNote.objects.create(
                user=request.user, course=course, lecture=lecture, image=img
            )

            try:
                extracted = extract_text_from_image(sn.image.path)
            except Exception as e:
                logger.exception("OCR failed for %s: %s", sn.image.path, e)
                extracted = "(Error extracting text)"

            sn.extracted_text = extracted
            sn.save()
            all_text_parts.append(extracted)

        combined_text = "\n\n".join(all_text_parts)

        # Generate AI Notes using Gemini
        try:
            generated_notes = structure_text_with_gemini(combined_text)
        except Exception as e:
            logger.exception("structure_text_with_gemini failed: %s", e)
            generated_notes = combined_text

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
            lecture=lecture,
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

    # If it already existed, update PDF and notes
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
'''
@login_required(login_url="login")
def download_lecture_notes_pdf(request, category_slug, course_slug, section, lecture):
    """
    Combine all LectureFinalNote.notes into a single PDF and return it.
    """
    course = Course.objects.filter(
        slug=course_slug, category__slug=category_slug, section=section
    ).first()
    if not course:
        return HttpResponse("Course not found.", status=404)

    lecture_notes_qs = LectureFinalNote.objects.filter(course=course, lecture=lecture)
    if not lecture_notes_qs.exists():
        return HttpResponse("No lecture notes found.", status=404)

    # Combine notes
    combined_md = ""
    for i, note in enumerate(lecture_notes_qs, start=1):
        combined_md += f"## Note {i}\n\n"
        combined_md += (note.notes or "(No notes)") + "\n\n"

    try:
        pdf_buffer = create_pdf_from_markdown_bytes(combined_md)
    except Exception as e:
        logger.exception("Failed to generate PDF: %s", e)
        return HttpResponse("Failed to generate PDF.", status=500)

    filename = f"{course.slug}_lecture_{lecture}_combined.pdf"
    return FileResponse(pdf_buffer, as_attachment=True, filename=filename, content_type="application/pdf")
'''
@login_required(login_url="login")
def download_user_images(request, user_id, category_slug, course_slug, section, lecture):
    """
    Create a ZIP containing enhanced images for a user for a specific lecture.
    Uses image_enhancer.utils.document_enhancer.enhance_document.
    """
    course = get_object_or_404(
        Course, slug=course_slug, category__slug=category_slug, section=section
    )

    notes = SectionNote.objects.filter(user_id=user_id, course=course, lecture=lecture)

    if not notes.exists():
        return HttpResponse("No images found for this user.", status=404)

    buffer = io.BytesIO()
    from image_enhancer.utils.document_enhancer import enhance_document

    with zipfile.ZipFile(buffer, "w") as zip_file:
        for note in notes:
            original_path = note.image.path
            enhanced_name = "enhanced_" + os.path.basename(original_path)

            # ensure outputs folder exists
            outputs_dir = os.path.join(settings.MEDIA_ROOT, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            enhanced_path = os.path.join(outputs_dir, enhanced_name)

            try:
                final_path = enhance_document(original_path, enhanced_path)
            except Exception as e:
                logger.exception("Image enhancement failed for %s: %s", original_path, e)
                # fallback: add original image
                final_path = original_path

            zip_file.write(final_path, arcname=enhanced_name)

    buffer.seek(0)
    filename = f"user_{user_id}_lecture_{lecture}_enhanced_images.zip"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type="application/zip")


def enhance_view(request):
    """
    API endpoint to enhance uploaded images (returns single enhanced image or a ZIP of enhanced images).
    """
    if request.method != "POST":
        return render(request, "course/lecture_detail.html")

    files = request.FILES.getlist("images")
    if not files:
        return HttpResponseBadRequest("No images uploaded.")

    output_files = []
    from image_enhancer.utils.document_enhancer import enhance_document

    # store temporary uploads using default_storage
    tmp_saved = []
    try:
        for file in files:
            tmp_name = default_storage.save(f"uploads/{file.name}", file)
            tmp_path = os.path.join(settings.MEDIA_ROOT, tmp_name)
            tmp_saved.append(tmp_name)

            outputs_dir = os.path.join(settings.MEDIA_ROOT, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            output_name = "enhanced_" + file.name
            output_path = os.path.join(outputs_dir, output_name)

            try:
                final_path = enhance_document(tmp_path, output_path)
            except Exception as e:
                logger.exception("Enhancement failed for %s: %s", tmp_path, e)
                final_path = tmp_path  # fallback to original
            output_files.append(final_path)

        # Single file -> return directly
        if len(output_files) == 1:
            return FileResponse(open(output_files[0], "rb"), content_type="image/png")

        # Multiple -> create a zip in memory
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, "w") as zf:
            for p in output_files:
                zf.write(p, os.path.basename(p))
        mem_zip.seek(0)
        return FileResponse(mem_zip, as_attachment=True, filename="enhanced_images.zip", content_type="application/zip")

    finally:
        # cleanup temp uploaded files
        for name in tmp_saved:
            try:
                default_storage.delete(name)
            except Exception:
                pass
