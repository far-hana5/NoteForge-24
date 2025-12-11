from django.apps import AppConfig

class CourseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'

    def ready(self):
        # import signals
        import courses.signals   # noqa
