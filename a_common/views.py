import os

from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from _config import settings
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


@login_not_required
def robots_txt(request):
    file_path = os.path.join(settings.BASE_DIR, 'robots.txt')
    with open(file_path, 'r') as file:
        content = file.read()
    return HttpResponse(content, content_type="text/plain")


@login_not_required
def login_modal_view(request: HtmxHttpRequest):
    context = update_context_data(next=request.htmx.current_url)
    return render(request, 'a_common/snippets/modal_login.html', context)


def logout_modal_view(request: HtmxHttpRequest):
    context = update_context_data(next=request.htmx.current_url)
    return render(request, 'a_common/snippets/modal_logout.html', context)


def changed_password_view(request: HtmxHttpRequest):
    context = update_context_data(changed=True)
    return render(request, 'account/password_change.html', context)


@login_not_required
def password_reset_done(request):
    return render(request, 'account/password_reset_done.html', {})


@login_not_required
def search_view(request: HtmxHttpRequest):
    exam_type = request.POST.get('exam_type')
    keyword = request.POST.get('keyword')

    if exam_type == '1':
        url = reverse_lazy('official:base')
        return redirect(f'{url}?keyword={keyword}')

    if exam_type == '2':
        url = reverse_lazy('daily:problem-list')
        return redirect(f'{url}?keyword={keyword}')

    if exam_type == '3':
        url = reverse_lazy('weekly:problem-list')
        return redirect(f'{url}?keyword={keyword}')
