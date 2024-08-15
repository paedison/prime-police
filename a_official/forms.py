from django import forms

from . import models


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = models.ProblemTag
        fields = ['name']


class ProblemCommentForm(forms.ModelForm):
    class Meta:
        model = models.ProblemComment
        fields = ['content', 'parent']


class ProblemMemoForm(forms.ModelForm):
    class Meta:
        model = models.ProblemMemo
        fields = ['content']


class ProblemCollectionForm(forms.ModelForm):
    title = forms.CharField(
        label='', label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': '컬렉션 이름'}
        )
    )

    class Meta:
        model = models.ProblemCollection
        fields = ['title']
