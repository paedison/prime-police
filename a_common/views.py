from allauth.account import views as allauth_views
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from .utils import HtmxHttpRequest, update_context_data


@login_not_required
def index_view(_):
    return redirect('official:base')


@login_not_required
def page_404(request):
    return render(request, 'a_common/404.html', {})


@login_not_required
def privacy(request):
    info = {'menu': 'privacy'}
    context = update_context_data(site_name='<PRIME 경위공채>', info=info)
    return render(request, 'a_common/privacy.html', context)


@method_decorator(login_not_required, name='dispatch')
class SignupView(allauth_views.SignupView):
    pass


@method_decorator(login_not_required, name='dispatch')
class LoginView(allauth_views.LoginView):
    pass


@method_decorator(login_not_required, name='dispatch')
class AccountInactiveView(allauth_views.AccountInactiveView):
    pass


@login_not_required
def login_modal_view(request: HtmxHttpRequest):
    context = update_context_data(next=request.htmx.current_url)
    return render(request, 'a_common/snippets/modal_login.html', context)


def logout_modal_view(request: HtmxHttpRequest):
    context = update_context_data(next=request.htmx.current_url)
    return render(request, 'a_common/snippets/modal_logout.html', context)


class PasswordChangeView(allauth_views.PasswordChangeView):
    success_url = reverse_lazy('changed_password')


def changed_password_view(request):
    context = update_context_data(changed=True)
    return render(request, 'account/password_change.html', context)
