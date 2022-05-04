from django.apps import AppConfig


# Name app in the Config with the package name appended to it to avoid conflicting import paths error.
class PressDirectoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "lib_metadata_db.press_directories"