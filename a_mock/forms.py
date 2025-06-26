from datetime import time, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.timezone import make_aware

from . import models


class ExamForm(forms.ModelForm):
    exam_date = forms.DateField(
        label='시험일', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_start_time = forms.TimeField(
        label='시험 시작 시각', initial=time(9, 10),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    exam_finish_time = forms.TimeField(
        label='시험 종료 시각', initial=time(11, 30),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_file = forms.FileField(
        label='정답 파일',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = models.Exam
        fields = ['year', 'exam_date', 'exam_start_time', 'exam_finish_time', 'answer_file']
        widgets = {'year': forms.TextInput(attrs={'class': 'form-control'})}

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

    def save(self, commit=True):
        instance = super().save(commit=False)
        cleaned_data = self.clean()
        instance.is_active = True
        instance.page_opened_at = cleaned_data['page_opened_at']
        instance.exam_started_at = cleaned_data['exam_started_at']
        instance.exam_finished_at = cleaned_data['exam_finished_at']
        if commit:
            instance.save()
        return instance


class UploadFileForm(forms.Form):
    file = forms.FileField(label='업로드 파일', widget=forms.FileInput(attrs={'class': 'form-control'}))


class StudentForm(forms.ModelForm):
    serial = forms.CharField(
        label='수험번호', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '수험번호'}),
        error_messages={'required': '수험번호를 입력해주세요.'},
    )
    name = forms.CharField(
        label='이름', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '이름'}),
        error_messages={'required': '이름을 입력해주세요.'},
    )
    password = forms.CharField(
        label='비밀번호', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '비밀번호'}),
        error_messages={'required': '비밀번호를 입력해주세요.'},
    )

    class Meta:
        model = models.Student
        fields = ['serial', 'name', 'password']


def get_local_time(target_date, target_time):
    if not target_date:
        raise ValidationError("Date is required for timezone conversion.")
    target_datetime = datetime.combine(target_date, target_time)
    return make_aware(target_datetime)
