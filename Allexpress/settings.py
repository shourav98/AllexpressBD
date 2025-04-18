from pathlib import Path
import environ
from django.contrib.messages import constants as messages

# Initialize the environment variables
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = env('SECRET_KEY')

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = [
    "allexpressbd-1.onrender.com",
    "localhost",
    "127.0.0.1",
    "*.ngrok.io",
    "*.ngrok-free.app",
    "5983-103-174-189-33.ngrok-free.app",  # Add the exact ngrok URL
]

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://sandbox.sslcommerz.com',
    'http://127.0.0.1',
    'https://*.ngrok.io',
    'https://*.ngrok-free.app',
    'https://5983-103-174-189-33.ngrok-free.app',  # Add the exact ngrok URL
])

# Add BASE_URL (replace with your ngrok URL or production URL)
BASE_URL = env('BASE_URL', default='https://5983-103-174-189-33.ngrok-free.app')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'category',
    'accounts',
    'store',
    'carts',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'Allexpress.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'category.context_processors.menu_links',
                'carts.context_processors.counter',
            ],
        },
    },
]

WSGI_APPLICATION = 'Allexpress.wsgi.application'
AUTH_USER_MODEL = 'accounts.Account'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    'Allexpress/static'
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MESSAGE_TAGS = {
    messages.ERROR: "danger",
}

# SSLCommerz configuration
SSLCOMMERZ_STORE_ID = env('SSLCOMMERZ_STORE_ID')
SSLCOMMERZ_STORE_PASS = env('SSLCOMMERZ_STORE_PASS')

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sir665904@gmail.com'
EMAIL_HOST_PASSWORD = 'khaq gdcs mfoc gfes'
DEFAULT_FROM_EMAIL = 'sir665904@gmail.com'



# from pathlib import Path
# import environ
# from django.contrib.messages import constants as messages

# # Initialize the environment variables
# env = environ.Env()
# environ.Env.read_env()  # Read the .env file if it exists

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent

# # Quick-start development settings - unsuitable for production
# # See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = env('SECRET_KEY')

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = env.bool('DEBUG', default=True)

# ALLOWED_HOSTS = ["allexpressbd-1.onrender.com", "localhost", "127.0.0.1"]

# # ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

# CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
#     'https://sandbox.sslcommerz.com',  # Add SSLCommerz domain here
#     'http://127.0.0.1',  # If using local testing
# ])

# # Application definition

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'category',
#     'accounts',
#     'store',
#     'carts',
#     'orders',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware',
# ]

# ROOT_URLCONF = 'Allexpress.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': ['templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#                 'category.context_processors.menu_links',
#                 'carts.context_processors.counter',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'Allexpress.wsgi.application'
# AUTH_USER_MODEL = 'accounts.Account'

# # Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]

# # Internationalization
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'
# USE_I18N = True
# USE_TZ = True

# # Static files (CSS, JavaScript, Images)
# STATIC_URL = 'static/'
# STATIC_ROOT = BASE_DIR / 'static'
# STATICFILES_DIRS = [
#     'Allexpress/static'
# ]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# # Default primary key field type
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# MESSAGE_TAGS = {
#     messages.ERROR: "danger",
# }

# # SSLCommerz configuration
# SSLCOMMERZ_STORE_ID = env('SSLCOMMERZ_STORE_ID')
# SSLCOMMERZ_STORE_PASS = env('SSLCOMMERZ_STORE_PASS')


# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True  
# EMAIL_HOST_USER = 'sir665904@gmail.com'
# EMAIL_HOST_PASSWORD = 'khaq gdcs mfoc gfes'
# DEFAULT_FROM_EMAIL = 'sir665904@gmail.com'




























# """
# Django settings for Allexpress project.

# Generated by 'django-admin startproject' using Django 4.2.3.

# For more information on this file, see
# https://docs.djangoproject.com/en/4.2/topics/settings/

# For the full list of settings and their values, see
# https://docs.djangoproject.com/en/4.2/ref/settings/
# """

# from pathlib import Path
# from decouple import config

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent


# # Quick-start development settings - unsuitable for production
# # See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = config("SECRET_KEY")

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config("DEBUG", default=True, cast=bool)

# ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
# CSRF_TRUSTED_ORIGINS = [
#     'https://sandbox.sslcommerz.com',  # Add SSLCommerz domain here
#     'http://127.0.0.1',  # If using local testing
# ]


# # Application definition

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'category',
#     'accounts',
#     'store',
#     'carts',
#     'orders',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'Allexpress.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': ['templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#                 'category.context_processors.menu_links',
#                 'carts.context_processors.counter',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'Allexpress.wsgi.application'
# AUTH_USER_MODEL = 'accounts.Account'


# # Database
# # https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# # Password validation
# # https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Internationalization
# # https://docs.djangoproject.com/en/4.2/topics/i18n/

# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

# USE_I18N = True

# USE_TZ = True


# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/4.2/howto/static-files/

# STATIC_URL = 'static/'
# STATIC_ROOT = BASE_DIR /'static'
# STATICFILES_DIRS = [
#     'Allexpress/static'
# ]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR /'media'

# # Default primary key field type
# # https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# from django.contrib.messages import constants as messages
# MESSAGE_TAGS = {
#     messages.ERROR: "danger",
# }


# SSLCOMMERZ_STORE_ID = 'jutah67162911b7845'
# SSLCOMMERZ_STORE_PASS = 'jutah67162911b7845@ssl'

# EMAIL_BACKEND = config("EMAIL_BACKEND")
# EMAIL_HOST = config("EMAIL_HOST")
# EMAIL_PORT = config("EMAIL_PORT", cast=int)
# EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool)
# EMAIL_HOST_USER = config("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
# SECRET_KEY = config("SECRET_KEY")

# SSLCOMMERZ_STORE_ID = 'jutah67162911b7845'
# SSLCOMMERZ_STORE_PASS = 'jutah67162911b7845@ssl'



# # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# # EMAIL_HOST = 'smtp.gmail.com'
# # EMAIL_PORT = 587
# # EMAIL_USE_TLS = True
# # EMAIL_HOST_USER = 'sir665904@gmail.com'

# # EMAIL_HOST_PASSWORD = 'kdtf ispy wkau cvgu'
# # SECRET_KEY = 'django-insecure-yaqzrots*1_ssf6ac&y3fg0ix5_pz#^clcf-40@u3ilb7l0w*1'






