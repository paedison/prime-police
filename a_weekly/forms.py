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


class OfflineAnswerInputForm(forms.Form):
    semester = forms.ChoiceField(
        choices=models.semester_choice(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='기수',
        required=True,
    )
    circle = forms.ChoiceField(
        choices=models.circle_choice(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='순환',
        required=True,
    )
    subject = forms.ChoiceField(
        choices=models.subject_choice(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='과목',
        required=True,
    )
    round = forms.ChoiceField(
        choices=models.round_choice(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='회차',
        required=True,
    )
    answer_file = forms.FileField(
        label='답안 파일',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
