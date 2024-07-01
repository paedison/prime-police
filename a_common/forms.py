from django import forms
from django.utils.translation import gettext_lazy as _

from a_common.models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['image']
        widgets = {
            'image': forms.FileInput(),
        }


class ChangeUsernameForm(forms.ModelForm):
    username = forms.CharField(
        label=_('Enter New Username'),
        widget=forms.TextInput(
            attrs={
                "placeholder": _('Enter New Username'),
            }
        )
    )

    class Meta:
        model = User
        fields = ('username',)
