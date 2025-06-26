from pathlib import Path

from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from environ import Env

env = Env(
    ENVIRONMENT=(str, 'ENVIRONMENT'),
    ALLOWED_HOSTS=(list, 'ALLOWED_HOSTS'),
    SECRET_KEY=(str, 'SECRET_KEY'),

    # Database Settings
    DB_ENGINE=(str, 'DB_ENGINE'),
    DB_NAME=(str, 'DB_NAME'),
    DB_USER=(str, 'DB_USER'),
    DB_PASSWORD=(str, 'DB_PASSWORD'),
    DB_HOST=(str, 'DB_HOST'),
    DB_PORT=(str, 'DB_PORT'),

    # Mail Settings
    EMAIL_HOST=(str, 'EMAIL_HOST'),
    EMAIL_PORT=(str, 'EMAIL_PORT'),
    EMAIL_HOST_USER=(str, 'EMAIL_HOST_USER'),
    EMAIL_HOST_PASSWORD=(str, 'EMAIL_HOST_PASSWORD'),
    EMAIL_USE_SSL=(bool, 'EMAIL_USE_SSL'),
    EMAIL_USE_TLS=(bool, 'EMAIL_USE_TLS'),
)
Env.read_env()
ENVIRONMENT = env('ENVIRONMENT', default='production')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if ENVIRONMENT == 'development' else False
INTERNAL_IPS = (
    '127.0.0.1',
    '127.0.0.1:8000',
    'localhost:8000',
)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['*'])


# Application definition
INSTALLED_APPS = [
    'unfold',

    # Default  //  Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Additionally Installed  //  Django Apps
    'django.contrib.sites',
    'django.contrib.humanize',

    # Third Party Apps
    'allauth',
    'allauth.account',
    'admin_honeypot',
    'ckeditor',
    'ckeditor_uploader',
    'crispy_forms',
    'django_filters',
    'django_htmx',
    'debug_toolbar',
    'template_partials',
    'slippers',
    'widget_tweaks',
    'django_extensions',

    # My Apps
    'a_common',
    'a_official',
    'a_daily',
    'a_board',
    'a_weekly',
    'a_infinite',
    'a_mock',

    'django_cleanup.apps.CleanupConfig',
]

MIDDLEWARE = [
    # Installed Additionally
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'allauth.account.middleware.AccountMiddleware',

    # Default Django Apps
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [(
                'django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]
            )],
            'builtins': [
                'template_partials.templatetags.partials',
                'slippers.templatetags.slippers',
                'a_common.templatetags.common_templatetags',
            ],
        },
    },
]

WSGI_APPLICATION = '_config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': env('DB_USER', default='user'),
        'PASSWORD': env('DB_PASSWORD', default='password'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default=''),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ko-KR'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True
LANGUAGES = [
    ('ko', _('Korean')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
if ENVIRONMENT == 'development':
    STATICFILES_DIRS = [
        BASE_DIR / 'static',
    ]
else:
    STATIC_ROOT = BASE_DIR / 'static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# DJANGO-Taggit
TAGGIT_CASE_INSENSITIVE = True
TAGGIT_LIMIT = 50
TAGGIT_TAG_LIST_ORDER_BY = 'name'


SITE_ID = 1


# Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env('EMAIL_HOST_USER')


# All auth configurations
AUTHENTICATION_BACKENDS = [
    # Needed to log in by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',  # Default Model Backend

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_ADAPTER = 'a_common.adapters.AccountAdapter'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[프라임 경위공채] '
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_FORMS = {
    'login': 'a_common.forms.LoginForm',
    'signup': 'a_common.forms.SignupForm',
    'change_password': 'a_common.forms.ChangePasswordForm',
    'reset_password': 'a_common.forms.ResetPasswordForm',
    'reset_password_from_key': 'a_common.forms.ResetPasswordKeyForm',
}
ACCOUNT_SESSION_COOKIE_AGE = 1209600
ACCOUNT_SIGNUP_FORM_HONEYPOT_FIELD = 'address'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_USERNAME_BLACKLIST = [
    'admin', 'administrator', 'account', 'accounts',
    'category', 'post', 'inbox', 'check_in_as_boss',
    'dashboard', 'profile', 'official', 'daily', 'common', 'notice', 'police',
]


# Custom User Model
AUTH_USER_MODEL = 'a_common.User'


# Session Setting
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'


# CkEditor Settings
CKEDITOR_BASEPATH = "/static/vendor/ckeditor/ckeditor/"
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = 'pillow'
X_FRAME_OPTIONS = "SAMEORIGIN"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript'],
            ['NumberedList', 'BulletedList', 'Blockquote', 'Code'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Embed', 'Table', 'HorizontalRule', 'SpecialChar'],
            ['Styles', 'Format', 'Font', 'FontSize'],
            ['TextColor', 'BGColor'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['RemoveFormat', 'Source'],
        ],
        'width': 'auto',
        "removePlugins": "stylesheetparser",
        'extraPlugins': ','.join([
            'autolink',
            'autoembed',
            'embed',
            'stylescombo',
        ]),
        'embed_provider': 'ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}',
    },
    'problem': {
        'toolbar': [
            ['Styles'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Undo', 'Redo'],
            ['Image', 'Table', 'SpecialChar'],
        ],
        # 'width': '100%',
        "removePlugins": "stylesheetparser",
        'extraPlugins': ','.join([
            'autolink',
            'autoembed',
            'embed',
            'stylescombo',
        ]),
        'table_defaultAttribs': {
            'border': '1',
            'cellpadding': '5',
            'cellspacing': '0',
            'width': '100%',
        },
        'stylesSet': 'custom_styles:/static/js/ckeditor_custom_config.js',
        'contentsCss': '/static/css/ckeditor_custom_styles.css',
        'embed_provider': 'ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}',
    },
    'minimal': {
        'toolbar': [
            ['Bold', 'Italic', 'Underline', 'Strike'],
            ['NumberedList', 'BulletedList', 'Outdent', 'Indent'],
        ],
        'width': 'auto',
        'height': 100,
        "removePlugins": "stylesheetparser",
    },
}


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'log/default.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins', 'file'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}


# django-debug-toolbar settings
DEBUG_TOOLBAR_CONFIG = {
    'ROOT_TAG_EXTRA_ATTRS': 'hx-preserve',
}
DEBUG_TOOLBAR_PANELS = [
    # 'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.alerts.AlertsPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

# Unfold settings
UNFOLD = {
    'STYLES': [
        lambda request: static('css/admin_custom.css'),
    ],
}