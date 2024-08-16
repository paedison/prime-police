from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.templatetags.static import static
from django.utils import timezone
from django_resized import ResizedImageField


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("이메일을 입력해주세요.")
        user = self.model(email=self.normalize_email(email), username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(email, username=username, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()
    username_validator = UnicodeUsernameValidator()

    email = models.EmailField('이메일', max_length=255, unique=True)
    username = models.CharField(
        '아이디', max_length=150, unique=True,
        help_text='150자 이하 문자, 숫자 그리고 @/./+/-/_만 가능합니다.',
        validators=[username_validator],
        error_messages={"unique": '해당 아이디는 이미 존재합니다.'})
    joined_at = models.DateTimeField('가입일', default=timezone.now)
    is_active = models.BooleanField(
        '활성', default=False,
        help_text="이 사용자가 활성화되어 있는지를 나타냅니다. 계정을 삭제하는 대신 이것을 선택 해제하세요.")
    is_staff = models.BooleanField(
        '스탭 권한', default=False,
        help_text='사용자가 관리사이트에 로그인이 가능한지를 나타냅니다.')
    image = ResizedImageField(size=[600, 600], quality=85, upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.email

    @property
    def avatar(self):
        if self.image:
            return self.image.url
        return static('image/undraw_profile.jpg')
