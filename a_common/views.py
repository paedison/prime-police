from allauth.account import views as allauth_views
from allauth.account.views import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic as generic_views

from . import forms as common_forms
from .models import User
from .utils import HtmxHttpRequest


def profile_view(request, username=None):
    if username:
        profile = get_object_or_404(User, username=username)
    else:
        try:
            profile = request.user
        except AttributeError:
            raise Http404()

    # posts = profile.user.posts.all()

    # if request.htmx:
    #     if 'top-posts' in request.GET:
    #         posts = profile.user.posts.annotate(
    #             num_likes=Count('likes')
    #         ).filter(num_likes__gt=0).order_by('-num_likes')
    #     elif 'top-comments' in request.GET:
    #         comments = profile.user.comments.annotate(
    #             num_likes=Count('likes')
    #         ).filter(num_likes__gt=0).order_by('-num_likes')
    #         reply_form = post_forms.ReplyCreateForm
    #         context = {
    #             'comments': comments,
    #             'reply_form': reply_form,
    #         }
    #         return render(request, 'a_common/snippets/loop_profile_comments.html', context)
    #     elif 'liked-posts' in request.GET:
    #         posts = profile.user.liked_posts.order_by('-likedpost__created')
    #     return render(request, 'a_common/snippets/loop_profile_posts.html', {'posts': posts})

    # new_message_form = inbox_forms.InboxNewMessageForm()

    context = {
        'profile': profile,
        # 'posts': posts,
        # 'new_message_form': new_message_form,
    }
    return render(request, 'a_common/profile.html', context)


@login_required
def profile_edit_view(request):
    # form = user_forms.ProfileForm(instance=request.user.profile)
    #
    # if request.method == 'POST':
    #     form = user_forms.ProfileForm(request.POST, request.FILES, instance=request.user.profile)
    #     if form.is_valid():
    #         form.save()
    #         return redirect('profile')

    if request.path == reverse('profile-onboarding'):
        template_name = 'a_users/profile_onboarding.html'
    else:
        template_name = 'a_users/profile_edit.html'

    # context = {
    #     'form': form,
    # }
    context = {}
    return render(request, template_name, context)


@login_required
def profile_delete_view(request):
    user = request.user

    if request.method == 'POST':
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted, what a pity')
        return redirect('home')

    return render(request, 'a_users/profile_delete.html')



class OnlyLoggedInAllowedMixin(UserPassesTestMixin):
    request: HtmxHttpRequest

    def test_func(self):
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect('index')


def add_current_url_to_context(
        context: dict,
        request: HtmxHttpRequest,
        redirect_field_value='redirect_field_value'
):
    if request.htmx:
        current_url = request.htmx.current_url
        context[redirect_field_value] = current_url
    return context


class LoginModalView(generic_views.TemplateView):
    template_name = 'a_common/snippets/modal_login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_current_url_to_context(context, self.request, 'next')


class LogoutModalView(generic_views.TemplateView):
    template_name = 'a_common/snippets/modal_logout.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {'next': self.request.GET.get('next', '')}
        )
        return context


class LoginView(allauth_views.LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_current_url_to_context(context, self.request)


class SignupView(allauth_views.SignupView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_current_url_to_context(context, self.request)


class UsernameChangeView(
    OnlyLoggedInAllowedMixin,
    generic_views.UpdateView
):
    template_name = 'account/username_change.html'
    form_class = common_forms.ChangeUsernameForm
    success_url = reverse_lazy('account_profile')

    def get_object(self, **kwargs):
        return User.objects.get(id=self.request.user.id)

    def form_valid(self, form):
        user = User.objects.get(id=self.request.user.id)
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')
        if not user.check_password(password):
            messages.error(self.request, _('Incorrect password.'))
            return self.form_invalid(form)
        if username == user.username:
            messages.error(self.request, _('Same as current username.'))
            return self.form_invalid(form)
        messages.success(self.request, _('Username successfully updated.'))
        return super().form_valid(form)


class PasswordChangeView(
    OnlyLoggedInAllowedMixin,
    allauth_views.PasswordChangeView
):
    success_url = reverse_lazy('account_profile')


login_modal = LoginModalView.as_view()
logout_modal = LogoutModalView.as_view()
username_change = UsernameChangeView.as_view()
password_change = PasswordChangeView.as_view()
