from allauth.account import forms as allauth_forms
from django import forms


class LoginForm(allauth_forms.LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remember'].label = '이메일 저장'
        self.fields['remember'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['login'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


class SignupForm(allauth_forms.SignupForm):
    name = forms.CharField(
        label='이름', max_length=10, required=True,
        widget=forms.TextInput(attrs={'placeholder': '이름', 'class': 'form-control'})
    )
    prime_id = forms.CharField(
        label='프라임법학원 아이디', max_length=20, required=True,
        widget=forms.TextInput(attrs={'placeholder': '프라임법학원 아이디', 'class': 'form-control'})
    )
    serial = forms.CharField(
        label='응시번호', max_length=8, required=True,
        help_text='핸드폰 번호에서 010을 제외한 나머지 8자리를 입력해주세요',
        widget=forms.TextInput(attrs={'placeholder': '프라임법학원 아이디', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class ChangePasswordForm(allauth_forms.ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['oldpassword'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class ResetPasswordForm(allauth_forms.ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})


class ResetPasswordKeyForm(allauth_forms.ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
