__all__ = [
    'semester_default', 'answer_default', 'statistics_default',
    'semester_choice', 'circle_choice', 'round_choice',
    'subject_choice', 'number_choice', 'answer_choice',
    'rating_choice', 'get_remarks',
]

from datetime import datetime

import pytz


def semester_default():
    return 75


def answer_default():
    return [0 for _ in range(10)]


def statistics_default():
    return {"max": 0, "t10": 0, "t20": 0, "avg": 0}


def semester_choice() -> list:
    choice = [(semester, f'{semester}기') for semester in range(75, semester_default() + 1)]
    choice.reverse()
    return choice


def circle_choice() -> list:
    return [(circle, f'{circle}순환') for circle in range(1, 4)]


def round_choice() -> list:
    return [(_round, f'제{_round}회') for _round in range(1, 31)]


def subject_choice() -> dict:
    return {
        '형법': '형법', '경찰': '경찰학', '헌법': '헌법', '범죄': '범죄학',
        '형소': '형사소송법', '민법': '민법총칙',
    }


def number_choice() -> list:
    return [(number, f'{number}번') for number in range(1, 41)]


def answer_choice() -> dict:
    return {1: '①', 2: '②', 3: '③', 4: '④'}


def rating_choice() -> dict:
    return {1: '⭐️', 2: '⭐️⭐️', 3: '⭐️⭐️⭐️', 4: '⭐️⭐️⭐️⭐️', 5: '⭐️⭐️⭐️⭐️⭐️'}


def get_remarks(message_type: str, remarks: str | None) -> str:
    utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M')
    separator = '|' if remarks else ''
    if remarks:
        remarks += f"{separator}{message_type}_at:{utc_now}"
    else:
        remarks = f"{message_type}_at:{utc_now}"
    return remarks
