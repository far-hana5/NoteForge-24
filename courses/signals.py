from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from .models import LectureFinalNote, Course


# ---------------------------------------------------------
#  When a LectureFinalNote is created → schedule PDF time
# ---------------------------------------------------------
@receiver(post_save, sender=LectureFinalNote)
def set_next_pdf_time_on_create(sender, instance, created, **kwargs):
    if created and not instance.next_pdf_time:
        course = instance.course
        now = timezone.now()

        # If course has class_time → schedule next day same class time
        if course.class_time:
            next_day = (instance.created_at + timedelta(minutes=10)).date()   # testing: 10 mins
            dt_naive = datetime.combine(next_day, course.class_time)
            aware = timezone.make_aware(dt_naive, timezone.get_current_timezone())
            instance.next_pdf_time = aware

        else:
            # No class time → simply wait 10 minutes
            instance.next_pdf_time = now + timedelta(minutes=10)

        instance.save()


# ---------------------------------------------------------
# When Course.class_time changes → update pending lectures
# ---------------------------------------------------------
@receiver(pre_save, sender=Course)
def update_lectures_when_course_time_changes(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = Course.objects.get(pk=instance.pk)
    except Course.DoesNotExist:
        return

    # Only update if class time changed
    if old.class_time != instance.class_time:
        pending = LectureFinalNote.objects.filter(course=instance, is_generated=False)

        for lec in pending:
            if lec.created_at:
                nd = (lec.created_at + timedelta(minutes=10)).date()  # testing: 10 mins
                dt_naive = (
                    datetime.combine(nd, instance.class_time)
                    if instance.class_time else None
                )
                if dt_naive:
                    aware = timezone.make_aware(dt_naive, timezone.get_current_timezone())
                    lec.next_pdf_time = aware
                    lec.save()
