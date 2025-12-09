from django.contrib import admin

# Register your models here.
from .models import Course, SectionNote

# Show images and details in admin
@admin.register(SectionNote)
class SectionNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "lecture", "uploaded_at", "image")
    list_filter = ("course", "lecture", "uploaded_at", "user")
    search_fields = ("course__course_name", "user__username", "lecture")
'''
    # Add a small preview of the image
    def image_tag(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" />'
        return "(No image)"
    image_tag.allow_tags = True
    image_tag.short_description = "Image Preview"
'''

class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields={'slug':('course_initial',)}
    list_display=('course_name','course_initial','faculty_initial')

admin.site.register(Course,CourseAdmin)
