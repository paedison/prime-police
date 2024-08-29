from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden


def permission_or_staff_required(perm, login_url=None, raise_exception=False):
    def check_perms(user):
        if user.has_perm(perm) or user.is_staff:
            return True
        if raise_exception:
            raise PermissionDenied
        return False

    return user_passes_test(check_perms, login_url=login_url)


def staff_required(view_func):
    """
    Decorator that requires the user to be a staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("You are not authorized to view this page.")
    return _wrapped_view
