from celery import shared_task
from django.utils import timezone
from .models import LectureFinalNote, SectionNote
from .utils import generate_final_pdf_from_notes  # we'll create this util
from django.core.exceptions import ObjectDoesNotExist

@shared_task
def process_due_lectures_task():
    now = timezone.now()
    pending = LectureFinalNote.objects.filter(is_generated=False, next_pdf_time__lte=now)
    for lec in pending:
        try:
            # generate_final_pdf_from_notes returns file path or file-like ContentFile
            generate_final_pdf_from_notes(lec)
            lec.is_generated = True
            lec.save()
        except Exception as e:
            # log error; don't mark generated so it can retry next run
            print(f"Error generating PDF for {lec}: {e}")
