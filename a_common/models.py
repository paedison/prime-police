from django.contrib.auth import models as auth_models
from django.db import models
from django.utils import timezone


class UserManager(auth_models.BaseUserManager):
    def create_user(self, email, name, prime_id, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일을 입력해주세요.')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, prime_id=prime_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, prime_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('슈퍼유저는 반드시 "is_staff=True"여야 합니다.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('슈퍼유저는 반드시 "is_superuser=True"여야 합니다.')

        return self.create_user(email, name, prime_id, password, **extra_fields)


class User(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, verbose_name='이메일')
    name = models.CharField(max_length=10, default='', verbose_name='이름')
    prime_id = models.CharField(max_length=20, default='', verbose_name='프라임법학원 아이디')
    joined_at = models.DateTimeField(default=timezone.now, verbose_name='가입일')
    is_active = models.BooleanField(
        help_text='이 사용자가 활성화되어 있는지를 나타냅니다. 계정을 삭제하는 대신 이 옵션을 해제하세요.',
        default=True, verbose_name='활성')
    is_staff = models.BooleanField(
        help_text='관리사이트 로그인 가능 여부를 나타냅니다.', default=False, verbose_name='스탭')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'prime_id']

    class Meta:
        ordering = ['id']
        verbose_name = verbose_name_plural = "사용자"

    def __str__(self):
        return f'{self.name}({self.email})'
