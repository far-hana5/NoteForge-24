from django.db import models
from category.models import CourseCategory
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
# Create your models here.


class Course(models.Model):
    
    course_name = models.CharField(max_length=500)
    course_initial = models.CharField(max_length=10)
    slug = models.SlugField(max_length=10)
    faculty_name = models.CharField(max_length=300, blank=True)
    faculty_initial = models.CharField(max_length=50)
    section = models.PositiveIntegerField(default=1)
    
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE)

    

    def get_url(self):
        return reverse('course_detail',args=[self.category.slug,self.slug,self.section])
    
    


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
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'lecture')  # prevents duplicates

    def __str__(self):
        return f"{self.course.course_name} - L{self.lecture}"
