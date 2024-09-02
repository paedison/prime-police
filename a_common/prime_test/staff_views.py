import itertools

import pandas as pd
from django.shortcuts import render, redirect
from django_htmx.http import replace_url

from .. import utils
from ..decorators import staff_required


@staff_required
def menu_list_view(request: utils.HtmxHttpRequest, config):
    context = utils.update_context_data(config=config)
    return render(request, 'a_common/prime_test/staff_list.html', context)


@staff_required
def exam_create_view(request: utils.HtmxHttpRequest, models, forms, config):
    if request.method == 'POST':
        form = forms.ExamForm(request.POST, request.FILES)
        if form.is_valid():
            exam = form.save()
            exam_info = {
                'semester': exam.semester, 'circle': exam.circle,
                'subject': exam. subject, 'round': exam.round,
            }
            answer_file = request.FILES['answer_file']
            df = pd.read_excel(answer_file, sheet_name='정답', header=0, index_col=0)

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

            df.replace(to_replace=replace_dict, inplace=True)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)
            answer_list = df.get('정답')
            for number, answer in answer_list.items():
                models.Problem.objects.get_or_create(number=number, answer=answer, **exam_info)

            response = redirect('daily:staff-menu')
            return replace_url(response, config.url_list)
        else:
            context = utils.update_context_data(config=config, form=form)
            return render(request, 'a_common/prime_test/staff_exam_create.html', context)

    form = forms.ExamForm()
    context = utils.update_context_data(config=config, form=form)
    return render(request, 'a_common/prime_test/staff_exam_create.html', context)
