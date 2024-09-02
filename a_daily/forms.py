from django import forms

from . import models


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = models.ProblemTag
        fields = ['name']


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


class ExamForm(forms.ModelForm):
    answer_file = forms.FileField(
        label='정답 파일',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = models.Exam
        fields = ['semester', 'circle', 'subject', 'round', 'opened_at', 'answer_file']
        widgets = {
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'circle': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'round': forms.Select(attrs={'class': 'form-select'}),
            'opened_at': forms.DateTimeInput(attrs={'class': 'form-control'}),
        }
