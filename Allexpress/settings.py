from pathlib import Path
import environ
from django.contrib.messages import constants as messages
from django.templatetags.static import static
# from decouple import config

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

import os
env = environ.Env()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize the environment variables
env = environ.Env()
env.read_env(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
SECRET_KEY = env('SECRET_KEY')

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS')


# Add BASE_URL (replace with your ngrok URL or production URL)
BASE_URL = env('BASE_URL', default='https://47aa47631504.ngrok-free.app')

# Application definition
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.inlines',

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
    'parcel',
  
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

# DATABASES for mysql
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': env('DB_NAME'),   
#         'USER': env('DB_USER'),
#         'PASSWORD': env('DB_PASSWORD'),
#         'HOST': env('DB_HOST'),
#         'PORT': env('DB_PORT'),


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


TIME_ZONE = 'Asia/Dhaka'
USE_TZ = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'pathao_errors.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Internationalization
LANGUAGE_CODE = 'en-us'
USE_I18N = True


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




# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env.int('EMAIL_PORT')
# EMAIL_USE_SSL = env('EMAIL_USE_SSL')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')



ADMIN_EMAIL = env('ADMIN_EMAIL')



PATHAO_BASE_URL = env('PATHAO_BASE_URL')
PATHAO_CLIENT_ID = env('PATHAO_CLIENT_ID')
PATHAO_CLIENT_SECRET = env('PATHAO_CLIENT_SECRET')
PATHAO_USERNAME = env('PATHAO_USERNAME')
PATHAO_PASSWORD = env('PATHAO_PASSWORD')
PATHAO_STORE_ID = env('PATHAO_STORE_ID')
GRANT_TYPE = 'password'



UNFOLD = {
    "SITE_LOGO": {
        "light": lambda request: static("images/e_com.png"),  # light mode
        "dark": lambda request: static("images/e_com.png"),  # dark mode
    },
    "SITE_DROPDOWN": [
        {
            "icon": "diamond",
            "title": _("My site"),
            "link": "https://example.com",
            "attrs": {
                "target": "_blank",
            },
        },
        {
            "icon": "diamond",
            "title": _("My site"),
            "link": reverse_lazy("admin:index"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SITE_TITLE": "Ecommerce Admin",
    "SITE_HEADER": "Ecommerce Administration",
    "SITE_URL": "/admin/",
    "SITE_ICON": {
        "light": lambda request: static("icon-light.png"),
        "dark": lambda request: static("icon-dark.png"),
    },
    "SITE_SYMBOL": "store",
 
    "SHOW_VIEW_ON_SITE": True,
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
        },
    },

    "SIDEBAR": {
        "show_search": True,  # Enable search inside sidebar
        "items": [
            {
                "label": "Dashboard",
                "icon": "heroicons-outline:home",
                "url": "/admin/",
            },
            {
                "label": "Users",
                "icon": "heroicons-outline:users",
                "models": [
                    "accounts.account",
                    "accounts.userprofile",
                ],
            },
            {
                "label": "Products",
                "icon": "heroicons-outline:archive-box",
                "models": [
                    "store.category",
                    "store.brand",
                    "store.product",
                    "store.variation",
                    "store.reviewrating",
                    "store.productgallery",
                ],
            },
            {
                "label": "Inventory",
                "icon": "heroicons-outline:clipboard-document-check",
                "models": [
                    "store.inventorylog",  # 🔑 new logs model
                ],
            },
            {
                "label": "Parcel",
                "icon": "heroicons-outline:clipboard-document-check",
                "models": [
                    "parcel.shipment",  # 🔑 new logs model
                    "parcel.shipmentevent",
                    "parcel.courier",
                    "parcel.couriercredential",

                ],
            },
            {
                "label": "Orders",
                "icon": "heroicons-outline:shopping-cart",
                "models": [
                    "orders.order",
                    "orders.orderproduct",
                    "orders.payment",
                ],
            },
            {
                "label": "Carts",
                "icon": "heroicons-outline:shopping-bag",
                "models": [
                    "carts.cart",
                    "carts.cartitem",
                ],
            },
        ],
    },
    "DASHBOARD_CALLBACK": "Allexpress.utils.dashboard_callback",  # Adjust path to match your project structure (e.g., create utils.py in your main app)
}



# UNFOLD = {
#     "SITE_TITLE": "My Admin",
#     "SITE_HEADER": "My Project Administration",
#     "SITE_LOGO": "path/to/logo.png",  # Optional
#     "SHOW_HISTORY": True,
#     "SHOW_VIEW_ON_SITE": True,


#     "SIDEBAR": {
#         "show_search": True,   # enable search inside sidebar
#         "items": [
#             {
#                 "label": "Dashboard",
#                 "icon": "heroicons-outline:home",
#                 "url": "/admin/",
#             },
#             {
#                 "label": "Users",
#                 "icon": "heroicons-outline:users",
#                 "models": [
#                     "accounts.account",
#                     "accounts.userprofile",
#                 ],
#             },
#             {
#                 "label": "Products",
#                 "icon": "heroicons-outline:archive-box",
#                 "models": [
#                     "store.category",
#                     "store.brand",
#                     "store.product",
#                     "store.variation",
#                     "store.reviewrating",
#                 ],
#             },
#             {
#                 "label": "Orders",
#                 "icon": "heroicons-outline:shopping-cart",
#                 "models": [
#                     "orders.order",
#                     "orders.orderproduct",
#                     "orders.payment",
#                 ],
#             },
#             {
#                 "label": "Carts",
#                 "icon": "heroicons-outline:shopping-bag",
#                 "models": [
#                     "carts.cart",
#                     "carts.cartitem",
#                 ],
#             },
#         ],
#     },
# }



# UNFOLD = {
#     "SITE_TITLE": "My Admin",
#     "SITE_HEADER": "My Project Administration",
#     "SITE_LOGO": "path/to/logo.png",  # Optional
#     "SHOW_HISTORY": True,
#     "SHOW_VIEW_ON_SITE": True,
# }



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






