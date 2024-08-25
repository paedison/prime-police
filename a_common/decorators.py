from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def permission_and_staff_required(perm, login_url=None, raise_exception=False):
    def check_perms(user):
        if user.has_perm(perm) or user.is_staff:
            return True
        if raise_exception:
            raise PermissionDenied
        return False

    return user_passes_test(check_perms, login_url=login_url)
