"""
Django settings for SHA_GROUP project.

Generated by 'django-admin startproject' using Django 5.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)sxyl_nmbolesc)_9=jb9a1!cw3%49@94tb1y&%qehufro$ap='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition
#MARK: APPS
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'sha',
    'investors',  
    'rest_framework_simplejwt',
    'media_management', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SHA_GROUP.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SHA_GROUP.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
#MARK: DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sha_db',
        'USER': 'root',
        'PASSWORD': 'Pass@123',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ] 
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



# STATICFILES_DIRS = [BASE_DIR / "static"]

# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configure Django to use your custom User model
AUTH_USER_MODEL = 'sha.User' # Ensure this is 'sha.User'

#MARK: JWT settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 'DEFAULT_PERMISSION_CLASSES': (
    #     'rest_framework.permissions.IsAuthenticated', # Default to requiring authentication
    # ),
    'EXCEPTION_HANDLER': 'sha.utils.custom_exception_handler',
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
#MARK: DASHBOARD
JAZZMIN_SETTINGS = {
    "site_title": "SHA Admin",
    "site_header": "SHA Admin",
    "site_brand": "SHA",
    "site_logo": "accounts/img/logo1.jpg",
    "site_icon": "accounts/img/admin.jpg",
    "welcome_sign": "Welcome to SHA Admin",
    "copyright": "SHA Inc.",
    "search_model": ["sha.User"],
    "theme": "darkly",
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["sha","investors"],

    "icons": {
        "admin": "fas fa-shield-alt",  # Django Admin default icon
        "auth": "fas fa-users-cog",    # Auth app general icon
        "auth.user": "fas fa-user",    # Default user icon
        "auth.Group": "fas fa-users",  # Default group icon

        # Your 'sha' app (assuming it contains core user/profile logic)
        "sha": "fas fa-id-badge",            # Good general icon for core identity/profile
        "sha.User": "fas fa-user-circle",    # Specific icon for the User model
        "sha.UserProfileSettings": "fas fa-cog", # Cog for settings, or eye for visibility/control
        # Alternative for UserProfileSettings: "fas fa-sliders-h", "fas fa-cogs"

        # 'investors' app
        "investors": "fas fa-hand-holding-usd", # General icon for finance/investment
        "investors.Investor": "fas fa-chart-line", # A financial chart or growing line
        "investors.InvestmentServiceGroup": "fas fa-cubes", # Groups of services, or "fa-project-diagram"
        "investors.InterestRateSetting": "fas fa-percent",   # Percentage for interest rates
        # Alternative for InterestRateSetting: "fas fa-money-bill-wave", "fas fa-calculator"

        # 'media_management' app
        "media_management": "fas fa-photo-video", # General icon for media (good choice)
        "media_management.ImageUpload": "fas fa-upload", # Good choice for uploads
 
    },

    "changeform_format": "horizontal_tabs",  # tabbed sections like Strapi
    "changeform_format_overrides": {
        "sha.User": "horizontal_tabs"
    },

    "related_modal_active": True,  # Show related (add/edit) as modals
    # "theme": "darkly",  # Dark theme like Strapi
    # "theme": "slate",
    "show_ui_builder": False,  # Disable live builder in production
}
