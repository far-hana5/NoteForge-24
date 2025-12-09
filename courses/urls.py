

from django.urls import path
from . import views

urlpatterns = [
    path('', views.course, name='course'),

    # category filter
    path('<slug:category_slug>/', 
         views.course, 
         name='course_by_category'),
     path('<slug:category_slug>/<slug:course_slug>/<int:section>/', views.course_detail, name='course_detail'),

    # Lecture page (each lecture separate)
    path("<slug:category_slug>/<slug:course_slug>/<int:section>/<int:lecture>/",
         views.course_detail_per_section,
         name="course_detail_per_section"),

    path('<slug:category_slug>/<slug:course_slug>/<int:section>/<int:lecture>/download/',
         views.download_lecture_notes_pdf,
         name='download_lecture_notes_pdf'),

  
    path(
    'download-user-images/<int:user_id>/<slug:category_slug>/<slug:course_slug>/<int:section>/<int:lecture>/',
    views.download_user_images,
    name='download_user_images'
)


]
