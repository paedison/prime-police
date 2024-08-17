from django import forms

from . import models


class PostForm(forms.ModelForm):
    title = forms.CharField(
        label='제목', label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': '제목'}
        )
    )
    top_fixed = forms.BooleanField(
        label='상단 고정', label_suffix='',
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input'}
        )
    )
    is_hidden = forms.BooleanField(
        label='비밀글', label_suffix='',
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input'}
        )
    )

    class Meta:
        model = models.Post
        fields = ['title', 'content', 'top_fixed', 'is_hidden']


class CommentForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ['user', 'post', 'content']
