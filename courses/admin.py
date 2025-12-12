from django.contrib import admin
from .models import Course, SectionNote, LectureFinalNote

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course_initial", "course_name", "section", "class_time")
    prepopulated_fields = {"slug": ("course_initial",)}

    search_fields = ("course_name", "course_initial")

@admin.register(SectionNote)
class SectionNoteAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "lecture", "uploaded_at")
    list_filter = ("course", "lecture")

@admin.register(LectureFinalNote)
class LectureFinalNoteAdmin(admin.ModelAdmin):
    list_display = ("course", "lecture", "is_generated", "next_pdf_time", "created_at")
    readonly_fields = ("created_at",)
