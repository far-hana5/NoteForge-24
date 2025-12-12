from django.db import models
from category.models import CourseCategory
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

class Course(models.Model):
    course_name = models.CharField(max_length=500)
    course_initial = models.CharField(max_length=10)
    slug = models.SlugField(max_length=50)
    faculty_name = models.CharField(max_length=300, blank=True)
    faculty_initial = models.CharField(max_length=50)
    section = models.PositiveIntegerField(default=1)
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE)

    # NEW: schedule fields for Option A
    class_days = models.JSONField(default=list, blank=True)
    # e.g. ["Monday", "Wednesday"]
    class_time = models.TimeField(null=True, blank=True)
    # e.g. 14:40
    class Meta:
            unique_together = ('course_initial', 'course_name', 'section')

    
    def get_url(self):
        return reverse('course_detail', args=[self.category.slug, self.slug, self.section])

    def __str__(self):
        return f"{self.course_initial} - {self.course_name} (Section {self.section})"


class SectionNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="notes")
    lecture = models.PositiveIntegerField()
    image = models.ImageField(upload_to='section_uploads/')
    extracted_text = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.course_name} - Sec {self.course.section}, Lec {self.lecture}"


class LectureFinalNote(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecture = models.IntegerField()
    notes = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to="final_pdfs/", null=True, blank=True)

    # When to run PDF generation (next-day at same course.class_time)
    next_pdf_time = models.DateTimeField(null=True, blank=True)
    is_generated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'lecture')

    def __str__(self):
        return f"{self.course.course_name} - L{self.lecture}"
