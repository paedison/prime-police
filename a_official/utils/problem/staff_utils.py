__all__ = [
    'AdminListContext', 'AdminDetailContext',
    'AdminCreateContext', 'AdminUpdateContext',
    'get_custom_data', 'get_custom_icons',
]

import itertools
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd
from PIL import Image

from a_common.constants import icon_set
from a_common.models import User
from a_common.utils import get_paginator_context, HtmxHttpRequest
from a_common.utils.modify_models_methods import with_bulk_create_or_update, append_list_create
from a_official import models, filters, forms
from a_official.utils.common_utils import *


@dataclass(kw_only=True)
class AdminListContext:
    _request: HtmxHttpRequest

    def __post_init__(self):
        request_context = RequestContext(_request=self._request)
        self.sub_title = request_context.get_sub_title()
        self.view_type = request_context.view_type
        self.page_number = request_context.page_number
        self.filterset = filters.OfficialExamFilter(data=self._request.GET, request=self._request)

    def get_exam_context(self):
        exam_context = get_paginator_context(self.filterset.qs, self.page_number)
        for exam in exam_context['page_obj']:
            exam.updated_problem_count = sum(1 for prob in exam.problems.all() if prob.question and prob.data)
        return exam_context


@dataclass(kw_only=True)
class AdminDetailContext:
    _request: HtmxHttpRequest
    _exam: models.Exam

    def __post_init__(self):
        request_context = RequestContext(_request=self._request)
        exam_context = ExamContext(_exam=self._exam)
        self._model = ModelData()
        self.view_type = request_context.view_type
        self.page_number = request_context.page_number
        self.qs_problem = self._model.problem.objects.filtered_problem_by_leet(self._exam)
        self.subject_vars = exam_context.subject_vars

    def get_problem_context(self):
        return get_paginator_context(self.qs_problem, self.page_number)

    def get_answer_official_context(self):
        query_dict = defaultdict(list)
        for query in self.qs_problem.order_by('id'):
            query_dict[query.subject].append(query)
        return {
            sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
            for sub, (_, _, idx, _) in self.subject_vars.items()
        }


@dataclass(kw_only=True)
class AdminCreateContext:
    form: forms.ExamForm

    def __post_init__(self):
        self._model = ModelData()

    @with_bulk_create_or_update()
    def process_post_request(self):
        exam = self.form.save()
        list_create = []

        subject_list = [sub for sub in models.choices.subject_choice().keys()]
        for subject in subject_list:
            for number in range(1, 41):
                problem_info = {'exam': exam, 'year': exam.year, 'subject': subject, 'number': number}
                append_list_create(models.Problem, list_create, **problem_info)

        return models.Problem, list_create, [], []


@dataclass(kw_only=True)
class AdminUpdateContext:
    _request: HtmxHttpRequest
    _exam: models.Exam

    def process_post_request(self):
        file = self._request.FILES['file']
        df = pd.read_excel(file, header=0, index_col=0)

        answer_symbol = {'①': 1, '②': 2, '③': 3, '④': 4}
        keys = list(answer_symbol.keys())
        combinations = []
        for i in range(1, 6):
            combinations.extend(itertools.combinations(keys, i))

        replace_dict = {}
        for combination in combinations:
            key = ''.join(combination)
            value = int(''.join(str(answer_symbol[k]) for k in combination))
            replace_dict[key] = value

        df['answer'].replace(to_replace=replace_dict, inplace=True)
        df = df.infer_objects(copy=False)

        for index, row in df.iterrows():
            problem = models.Problem.objects.get(leet=self._exam, subject=row['subject'], number=row['number'])
            problem.paper_type = row['paper_type']
            problem.answer = row['answer']
            problem.question = row['question']
            problem.data = row['data']
            problem.save()


def create_img_wide(img, width, height, threshold_height, img_wide_path):
    target_height = 1500 if height < threshold_height + 500 else height // 2
    split_y = find_split_point(img, target_height)
    img1 = img.crop((0, 0, width, split_y))
    img2 = img.crop((0, split_y, width, height))

    width1, height1 = img1.size
    width2, height2 = img2.size
    new_width = width1 + width2
    new_height = max(height1, height2)

    img_wide = Image.new('RGB', (new_width, new_height), (255, 255, 255))
    img_wide.paste(img1, (0, 0))
    img_wide.paste(img2, (width1, 0))
    img_wide.save(img_wide_path, format='PNG')


def find_split_point(image, target_height=1000, margin=50) -> int:
    """target_height ± margin 내에서 여백(밝은 부분)을 찾아 분할 위치를 반환"""
    width, height = image.size
    crop_area = (0, max(0, target_height - margin), width, min(height, target_height + margin))
    cropped = image.crop(crop_area).convert('L')  # 밝기 기반

    pixels = cropped.load()
    scores = []
    for y in range(cropped.height):
        brightness = sum(pixels[x, y] for x in range(cropped.width))
        scores.append((brightness, y))

    # 밝은 부분 (여백) 우선
    best = max(scores, key=lambda x: x[0])
    split_y = crop_area[1] + best[1]
    return split_y


def get_custom_data(user: User) -> dict:
    def get_filtered_qs(model, *args):
        if not args:
            args = ['user', 'problem']
        qs = model.objects.filter(is_active=True).select_related(*args)

        if model == models.ProblemCollectionItem:
            return qs.filter(collection__user=user)
        return qs.filter(user=user)

    if user and user.is_authenticated:
        return {
            'like': get_filtered_qs(models.ProblemLike),
            'rate': get_filtered_qs(models.ProblemRate),
            'solve': get_filtered_qs(models.ProblemSolve),
            'memo': get_filtered_qs(models.ProblemMemo),
            'tag': get_filtered_qs(models.ProblemTaggedItem, *['user', 'content_object']),
            'collection': get_filtered_qs(models.ProblemCollectionItem, *['collection__user', 'problem']),
        }
    return {
        'like': [], 'rate': [], 'solve': [], 'memo': [], 'tag': [], 'collection': [],
    }


def get_custom_icons(problem: models.Problem, custom_data: dict):
    def get_status(status_type, field=None, default: bool | int | None = False):
        for dt in custom_data[status_type]:
            problem_id = getattr(dt, 'problem_id', getattr(dt, 'content_object_id', ''))
            if problem_id == problem.id:
                default = getattr(dt, field) if field else True
        return default

    is_liked = get_status(status_type='like', field='is_liked')
    rating = get_status(status_type='rate', field='rating', default=0)
    is_correct = get_status(status_type='solve', field='is_correct', default=None)
    is_memoed = get_status('memo')
    is_tagged = get_status('tag')
    is_collected = get_status('collection')

    problem.icon_like = icon_set.ICON_LIKE[f'{is_liked}']
    problem.icon_rate = icon_set.ICON_RATE[f'star{rating}']
    problem.icon_solve = icon_set.ICON_SOLVE[f'{is_correct}']
    problem.icon_memo = icon_set.ICON_MEMO[f'{is_memoed}']
    problem.icon_tag = icon_set.ICON_TAG[f'{is_tagged}']
    problem.icon_collection = icon_set.ICON_COLLECTION[f'{is_collected}']


def get_all_comments(queryset, problem_id=None):
    if problem_id:
        queryset = queryset.filter(problem_id=problem_id)
    parent_comments = queryset.filter(parent__isnull=True).order_by('-created_at')
    child_comments = queryset.exclude(parent__isnull=True).order_by('parent_id', '-created_at')
    all_comments = []
    for comment in parent_comments:
        all_comments.append(comment)
        all_comments.extend(child_comments.filter(parent=comment))
    return all_comments
