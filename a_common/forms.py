from allauth.account import forms as allauth_forms
from django import forms

from . import models


class LoginForm(allauth_forms.LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remember'].label = '이메일 저장'
        self.fields['remember'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['login'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


class SignupForm(allauth_forms.SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['email'].label = '이메일'
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        # self.fields['username'].label = '아이디'
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].label = '비밀번호'
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].label = '비밀번호(확인)'
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})



class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ['image']
        widgets = {
            'image': forms.FileInput(),
        }


class ChangeUsernameForm(forms.ModelForm):
    username = forms.CharField(
        label='아이디',
        widget=forms.TextInput(
            attrs={
                "placeholder": '새로운 아이디를 입력해주세요.',
            }
        )
    )

    class Meta:
        model = models.User
        fields = ('username',)
