from django.apps import AppConfig


class MedicaltutordjappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "medicaltutordjapp"
    
    def ready(self):
        import medicaltutordjapp.signals
