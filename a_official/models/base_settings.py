from datetime import datetime

import pytz
from django.db import models


def get_current_year():
    return datetime.now().year


def year_choices() -> list:
    choice = [(year, f'{year}년') for year in range(2023, get_current_year() + 2)]
    choice.reverse()
    return choice


def exam_choices() -> dict:
    return {
        '경위': '경위공채',
    }


def unit_choices() -> dict:
    return {
        '경위': '경위공채',
    }


def department_choices() -> dict:
    return {
        '일반': '일반',
        '세무': '세무회계',
        '사이': '사이버',
    }


def subject_choices() -> dict[str, dict[str, str]]:
    return {
        '전체 공통': {'형사': '형사법', '헌법': '헌법'},
        '일반 필수': {'경찰': '경찰학', '범죄': '범죄학'},
        '일반 선택': {'행법': '행정법', '행학': '행정학', '민법': '민법총칙'},
        '세무회계 필수': {'세법': '세법개론', '회계': '회계학'},
        '세무회계 선택': {'상법': '상법총칙', '경제': '경제학', '통계': '통계학', '재정': '재정학'},
        '사이버 필수': {'정보': '정보보호론', '시네': '시스템네트워크보안'},
        '사이버 선택': {'데베': '데이터베이스론', '통신': '통신이론', '소웨': '소프트웨어공학'},
    }


def number_choices() -> list:
    return [(number, f'{number}번') for number in range(1, 41)]


def rating_choices() -> dict:
    return {
        1: '⭐️',
        2: '⭐️⭐️',
        3: '⭐️⭐️⭐️',
        4: '⭐️⭐️⭐️⭐️',
        5: '⭐️⭐️⭐️⭐️⭐️',
    }


def answer_choices() -> dict:
    return {
        1: '①',
        2: '②',
        3: '③',
        4: '④',
    }


def get_remarks(message_type: str, remarks: str | None) -> str:
    utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M')
    separator = '|' if remarks else ''
    if remarks:
        remarks += f"{separator}{message_type}_at:{utc_now}"
    else:
        remarks = f"{message_type}_at:{utc_now}"
    return remarks


class TimeRecordField(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class RemarksField(models.Model):
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk is not None:
            message_type = kwargs.pop('message_type', '')
            self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ChoiceMethod:
    @staticmethod
    def get_exam_choices():
        return exam_choices()

    @staticmethod
    def get_subject_choices():
        return subject_choices()


class TimeRemarkChoiceBase(TimeRecordField, RemarksField, ChoiceMethod):
    class Meta:
        abstract = True


class TimeChoiceBase(TimeRecordField, ChoiceMethod):
    class Meta:
        abstract = True


class TimeRemarkBase(TimeRecordField, RemarksField):
    class Meta:
        abstract = True
