from datetime import time, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.timezone import make_aware

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
    exam_date = forms.DateField(
        label='시험일', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_start_time = forms.TimeField(
        label='시험 시작 시각', initial=time(14, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    exam_finish_time = forms.TimeField(
        label='시험 종료 시각', initial=time(17, 40),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_file = forms.FileField(
        label='정답 파일',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = models.Exam
        fields = ['semester', 'round', 'exam_date', 'exam_start_time', 'exam_finish_time', 'answer_file']
        widgets = {
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'round': forms.Select(attrs={'class': 'form-select'}),
            'opened_at': forms.DateTimeInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        try:
            exam_date = cleaned_data['exam_date']
            exam_start_time = cleaned_data['exam_start_time']
            exam_finish_time = cleaned_data['exam_finish_time']
        except KeyError as e:
            raise ValidationError(f"Missing field: {e.args[0]}")

        cleaned_data['page_opened_at'] = get_local_time(exam_date, exam_start_time)
        cleaned_data['exam_started_at'] = get_local_time(exam_date, exam_start_time)
        cleaned_data['exam_finished_at'] = get_local_time(exam_date, exam_finish_time)
        return cleaned_data


def get_local_time(target_date, target_time):
    if not target_date:
        raise ValidationError("Date is required for timezone conversion.")
    target_datetime = datetime.combine(target_date, target_time)
    return make_aware(target_datetime)


class UploadFileForm(forms.Form):
    file = forms.FileField(label='업로드 파일', widget=forms.FileInput(attrs={'class': 'form-control'}))
