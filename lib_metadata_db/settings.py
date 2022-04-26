import os

from dotenv import load_dotenv

load_dotenv()

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECRET_KEY = os.getenv("SECRET_KEY")

DATABASES = {
    "default": {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        "NAME": os.getenv("DB_NAME_NEWSPAPERS"),
        "USER": os.getenv("DB_USERNAME_NEWSPAPERS"),
        "PASSWORD": os.getenv("DB_PASSWORD_NEWSPAPERS"),
        "HOST": os.getenv("DB_HOST_NEWSPAPERS"),
        "PORT": os.getenv("PORT"),
        "ATOMIC_REQUESTS": True,
    },
    "newspapers_db": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME_NEWSPAPERS"),
        "USER": os.getenv("DB_USERNAME_NEWSPAPERS"),
        "PASSWORD": os.getenv("DB_PASSWORD_NEWSPAPERS"),
        "HOST": os.getenv("DB_HOST_NEWSPAPERS"),
        "PORT": os.getenv("PORT"),
        "ATOMIC_REQUESTS": True,
    },
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "newspapers.apps.NewspapersConfig",
    "press_directories.apps.PressDirectoriesConfig",
    "gazetteer.apps.GazetteerConfig",
]

USE_TZ = False
TIME_ZONE = "GB"
