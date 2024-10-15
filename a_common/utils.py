import traceback
from collections import Counter

import django
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest
from django_htmx.middleware import HtmxDetails

from .constants import icon_set
from .prime_test.model_settings import subject_choice, semester_default


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


def update_context_data(context: dict = None, **kwargs):
    if context:
        context.update(kwargs)
        return context
    return kwargs


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        first_bytes = f.read(3)
    return 'utf-8-sig' if first_bytes == b'\xef\xbb\xbf' else 'utf-8'


def get_page_obj_and_range(page_number, page_data, per_page=10):
    paginator = Paginator(page_data, per_page)
    page_obj = paginator.page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range


def get_sub_title(exam_circle, exam_round, exam_subject, end_string='문제') -> str:
    title_parts = []
    if exam_circle:
        title_parts.append(f'{exam_circle}순환')
    if exam_subject:
        title_parts.append(subject_choice()[exam_subject])
    if exam_round:
        title_parts.append(f'{exam_round}회차')
    if not exam_circle and not exam_round and not exam_subject:
        title_parts.append('전체')
    return f'{" ".join(title_parts)} {end_string}'


def get_prev_next_prob(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_prob = next_prob = None
    if custom_list:
        last_id = len(custom_list) - 1
        q = custom_list.index(pk)
        if q != 0:
            prev_prob = custom_data[q - 1]
        if q != last_id:
            next_prob = custom_data[q + 1]
    return prev_prob, next_prob


def get_list_data(queryset, student) -> list:
    list_data = []
    for data in queryset:
        if student and student.answer_student:
            data.is_correct = data.answer == student.answer_student[data.number - 1]
        list_data.append(data)
    return list_data


def get_custom_data(user, models) -> dict:
    if user.is_authenticated:
        return {
            'like': models.ProblemLike.objects.filter(user=user).select_related('user', 'problem'),
            'rate': models.ProblemRate.objects.filter(user=user).select_related('user', 'problem'),
            'solve': models.ProblemSolve.objects.filter(user=user).select_related('user', 'problem'),
            'memo': models.ProblemMemo.objects.filter(user=user).select_related('user', 'problem'),
            'tag': models.ProblemTaggedItem.objects.filter(
                user=user, active=True).select_related('user', 'content_object'),
            'collection': models.ProblemCollectionItem.objects.filter(
                collection__user=user).select_related('collection__user', 'problem'),
        }
    return {'like': [], 'rate': [], 'solve': [], 'memo': [], 'tag': [], 'collection': []}


def get_custom_icons(user, models, problem, exam_info, custom_data: dict):
    def get_status(status_type, field=None, default: bool | int | None = False):
        for dt in custom_data[status_type]:
            problem_id = getattr(dt, 'problem_id', getattr(dt, 'content_object_id', ''))
            if problem_id == problem.id:
                default = getattr(dt, field) if field else True
        return default

    is_liked = get_status(status_type='like', field='is_liked')
    rating = get_status(status_type='rate', field='rating', default=0)
    is_memoed = get_status('memo')
    is_tagged = get_status('tag')
    is_collected = get_status('collection')

    is_correct = None
    student: models.Student | None = models.Student.objects.filter(user=user, **exam_info).first()
    if student and student.answer_confirmed:
        is_correct = problem.answer == student.answer_student[problem.number - 1]

    problem.icon_like=icon_set.ICON_LIKE[f'{is_liked}']
    problem.icon_rate=icon_set.ICON_RATE[f'star{rating}']
    problem.icon_solve=icon_set.ICON_SOLVE[f'{is_correct}']
    problem.icon_memo=icon_set.ICON_MEMO[f'{is_memoed}']
    problem.icon_tag=icon_set.ICON_TAG[f'{is_tagged}']
    problem.icon_collection=icon_set.ICON_COLLECTION[f'{is_collected}']


def get_answer_rate(models, problem, exam_info):
    answer_count = models.AnswerCount.objects.filter(number=problem.number, **exam_info).first()
    rate_correct = getattr(answer_count, f'count_{problem.answer}') * 100 / answer_count.count_total
    difficulty = 'success'
    if 75 <= rate_correct < 90:
        difficulty = 'warning'
    if rate_correct < 75:
        difficulty = 'danger'
    problem.rate_correct = rate_correct
    problem.difficulty = difficulty


def get_exam_info(instance):
    return {
        'semester': semester_default(), 'circle': instance.circle,
        'subject': instance.subject, 'round': instance.round
    }


def get_student(request: HtmxHttpRequest, models, exam_info: dict):
    return models.Student.objects.filter(user=request.user, **exam_info).first()


def get_statistics(score_list: list, score: float) -> dict:
    participants = len(score_list)
    sorted_scores = sorted(score_list, reverse=True)
    try:
        rank = sorted_scores.index(score) + 1
        max_score = round(sorted_scores[0], 1)
        top_10_threshold = max(1, int(participants * 0.1))
        top_20_threshold = max(1, int(participants * 0.2))
        top_score_10 = round(sorted_scores[top_10_threshold - 1], 1)
        top_score_20 = round(sorted_scores[top_20_threshold - 1], 1)
        avg_score = round(sum(score_list) / participants if participants else 0, 1)
    except ValueError:
        rank = max_score = top_score_10 = top_score_20 = avg_score = None
    return {
        'participants': participants, 'rank': rank,
        'max': max_score, 't10': top_score_10, 't20': top_score_20, 'avg': avg_score,
    }


def get_answer_lists_by_rank(models, exam_info, rank_list, exam):
    top_rank_threshold = 0.27
    mid_rank_threshold = 0.73
    answer_lists_by_rank: dict[str, list] = {rnk: [] for rnk in rank_list}

    qs_student = models.Student.objects.filter(answer_confirmed=True, **exam_info)
    for student in qs_student:
        rank_ratio = student.rank / exam.participants if student.rank and exam.participants else None
        answer_lists_by_rank['all_rank'].append(student.answer_student)
        if rank_ratio:
            if 0 <= rank_ratio <= top_rank_threshold:
                answer_lists_by_rank['top_rank'].append(student.answer_student)
            elif top_rank_threshold < rank_ratio <= mid_rank_threshold:
                answer_lists_by_rank['mid_rank'].append(student.answer_student)
            elif mid_rank_threshold < rank_ratio <= 1:
                answer_lists_by_rank['low_rank'].append(student.answer_student)

    return answer_lists_by_rank


def get_answer_count_list(models, exam_info, rank_list, answer_lists_by_rank):
    problem_count = models.Problem.objects.filter(**exam_info).count()
    answer_count = []
    for number in range(1, problem_count + 1):
        problem_info = dict(exam_info, **{'number': number})
        problem_info.update({
            'data': {rnk: [] for rnk in rank_list}
        })
        answer_count.append(problem_info)

    for rnk, answer_lists in answer_lists_by_rank.items():
        distributions = [Counter() for _ in range(problem_count)]
        for lst in answer_lists:
            for i, value in enumerate(lst):
                if value > 4:
                    distributions[i]['count_multiple'] += 1
                else:
                    distributions[i][value] += 1

        for idx, counter in enumerate(distributions):
            count_list = [counter.get(i, 0) for i in range(5)]
            count_total = sum(count_list[1:])
            count_list.extend([counter.get('count_multiple', 0), count_total])
            answer_count[idx]['data'][rnk] = count_list

    return answer_count


def update_answer_count_model(models, exam_info, answer_count):
    update_list = []
    update_count = 0
    for answer_cnt in answer_count:
        try:
            obj = models.AnswerCount.objects.get(**exam_info, **{'number': answer_cnt['number']})
            obj.data = answer_cnt['data']
            update_list.append(obj)
            update_count += 1
        except models.AnswerCount.DoesNotExist:
            print(f'Instance is not created.')
        except models.AnswerCount.MultipleObjectsReturned:
            print(f'Instance is duplicated.')

    try:
        with transaction.atomic():
            if update_list:
                models.AnswerCount.objects.bulk_update(update_list, ['data'])
                message = f'문항 분석표가 업데이트되었습니다.'
            else:
                message = f'기존 문항 분석표와 동일합니다.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = '에러가 발생했습니다.'

    return message


def get_qs_answer_count_for_staff_answer_detail(models, exam_info, answer_official):
    qs_answer_count = models.AnswerCount.objects.filter(**exam_info).order_by('number').annotate(no=F('number'))

    for idx, answer_cnt in enumerate(qs_answer_count):
        ans_official = answer_official[idx]['ans']
        if 1 <= ans_official <= 5:
            rate_all_rank = getattr(answer_cnt, f'rate_{ans_official}')
        else:
            ans_official_list = [int(ans) for ans in str(ans_official)]
            rate_all_rank = sum(getattr(answer_cnt, f'rate_{ans}') for ans in ans_official_list)

        rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']
        for rnk in rank_list:
            ans_cnt = answer_cnt.data[rnk] if rnk in answer_cnt.data else []
            rate = 0
            try:
                if ans_cnt[-1]:
                    rate = round(ans_cnt[ans_official] * 100 / ans_cnt[-1], 1)
            except IndexError:
                pass
            setattr(answer_cnt, rnk, ans_cnt)
            setattr(answer_cnt, f'rate_{rnk}', rate)
        setattr(answer_cnt, 'rate_gap', answer_cnt.rate_top_rank - answer_cnt.rate_low_rank)

        answer_cnt.ans_official = ans_official
        answer_cnt.rate_all_rank = rate_all_rank

    return qs_answer_count


def update_student_model_for_score(models, exam_info):
    update_list = []
    update_count = 0

    answer_official = models.Problem.objects.filter(**exam_info).order_by('number').values_list('answer', flat=True)
    qs_student = models.Student.objects.filter(answer_confirmed=True, **exam_info)

    for student in qs_student:
        correct_cnt = sum(1 for x, y in zip(answer_official, student.answer_student) if x == y)
        score = round(correct_cnt * 100 / len(answer_official), 1)
        if student.score != score:
            student.score = score
            update_list.append(student)
            update_count += 1

    try:
        with transaction.atomic():
            if update_list:
                models.Student.objects.bulk_update(update_list, ['score'])
                message = f'{update_count}명의 점수가 업데이트되었습니다.'
            else:
                message = f'기존 점수 데이터와 동일합니다.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = '에러가 발생했습니다.'

    return message


def update_student_model_for_rank(models, exam, exam_info):
    update_list = []
    update_count = 0

    qs_student = models.Student.objects.filter(answer_confirmed=True, **exam_info)
    score_list = qs_student.values_list('score', flat=True)
    sorted_scores = sorted(score_list, reverse=True)

    if score_list:
        stat = get_statistics(score_list, score_list[0])
        stat.pop('rank')
        participants = stat.pop('participants')

        exam.participants = participants
        exam.statistics = stat
        exam.save()

    for student in qs_student:
        rank = sorted_scores.index(student.score) + 1
        if student.rank != rank:
            student.rank = rank
            update_list.append(student)
            update_count += 1

    try:
        with transaction.atomic():
            if update_list:
                models.Student.objects.bulk_update(update_list, ['rank'])
                message = f'{update_count}명의 석차가 업데이트되었습니다.'
            else:
                message = f'기존 석차 데이터와 동일합니다.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = '에러가 발생했습니다.'

    return message


def get_score_points(models, exam_info):
    score_points_list = list(models.Student.objects.filter(
        score__isnull=False, **exam_info).values_list('score', flat=True))
    score_points_list.sort()
    return Counter(score_points_list)
