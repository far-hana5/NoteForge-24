from django.contrib import admin

# Register your models here.

from .models import CourseCategory

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields={'slug':('dep_name',)}
    list_display=('courseCategory','dep_name')

admin.site.register(CourseCategory,CategoryAdmin)

