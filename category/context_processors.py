from .models import CourseCategory
def menu_links(request):
    links=CourseCategory.objects.all()
    return dict(links=links)
