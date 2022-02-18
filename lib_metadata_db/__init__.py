import os
import sys
import django


if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lib_metadata_db.settings")

    # Insert lib_metadat_db to system path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Setup the apps so that models can be immediately used on import
    django.setup()
