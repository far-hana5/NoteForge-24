from django.db import models
from django.urls import reverse

class CourseCategory(models.Model):
    courseCategory=models.CharField(max_length=200,default='CSE')
    dep_name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500)

    class Meta:
        verbose_name='category'
        verbose_name_plural='categories'
    def get_url(self):
        return reverse('course_by_category',args=[self.slug])
    
    

    def __str__(self):
        return f"{self.courseCategory}"
