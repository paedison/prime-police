from django import template

register = template.Library()


@register.filter
def add_space(content):  # Add Space before 1-Digit Number
    if int(content) < 10:
        content = " " + str(content)
    return content


@register.filter
def subtract(value, arg: int) -> int:  # Subtract arg from value
    return arg - int(value)


@register.filter
def digit_of_one(value) -> int:  # Convert to 2-Digit Number
    digit = abs(value) % 10
    if digit == 0:
        return digit + 10
    return digit


@register.filter(name='to_int')
def to_int(value) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0  # or handle the error as needed


@register.filter
def percentage(content) -> float:
    if content:
        return content * 100
    return 0


@register.filter
def percentageby(content, arg: int) -> float | str:
    if content:
        return content * 100 / arg
    return 0


@register.filter()
def to_kor_day(value: str):
    days = ['일', '월', '화', '수', '목', '금', '토']
    return days[int(value)]


@register.filter
def divide(content, base) -> float:  # Divide content by base
    return content / base
