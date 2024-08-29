from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        data = form.cleaned_data
        email = data.get('email')
        user_email(user, email)
        user.set_password(data["password1"])
        user.name = data.get('name')
        user.prime_id = data.get('prime_id')
        if commit:
            user.save()
        return user
