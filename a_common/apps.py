from django.apps import AppConfig


class ACommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_common'
    verbose_name = '0_기본'
