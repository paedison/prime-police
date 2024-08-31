from datetime import date

from django.db.models import F, Max, Case, When, BooleanField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from a_common.constants import icon_set
from a_common.decorators import permission_or_staff_required
from a_common import utils
from .. import models, forms, filters


class ProblemConfiguration:
    menu = 'weekly'
    submenu = 'problem'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '주간모의고사', 'eng': menu.capitalize()}
    submenu_title = {'kor': '오답 노트', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_weekly_problem_changelist')
    url_list = reverse_lazy(f'weekly:problem-list')
    url_create_collection = reverse_lazy('weekly:collection-create')


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def problem_list_view(request: utils.HtmxHttpRequest):
    config = ProblemConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_circle = request.GET.get('circle', '')
    exam_round = request.GET.get('round', '')
    exam_subject = request.GET.get('subject', '')
    page = request.GET.get('page', '1')

    sub_title = utils.get_sub_title(exam_circle, exam_round, exam_subject)

    if request.user.is_authenticated:
        filterset = filters.DailyProblemFilter(data=request.GET, request=request)
    else:
        filterset = filters.AnonymousDailyProblemFilter(data=request.GET, request=request)

    custom_data = utils.get_custom_data(request.user, models)
    page_obj, page_range = utils.get_page_obj_and_range(page, filterset.qs)
    for problem in page_obj:
        utils.get_custom_icons(request.user, models, problem, custom_data)
    context = utils.update_context_data(
        config=config, sub_title=sub_title, form=filterset.form,
        icon_menu=icon_set.ICON_MENU['weekly'], icon_image=icon_set.ICON_IMAGE,
        custom_data=custom_data, page_obj=page_obj, page_range=page_range,
    )
    if view_type == 'problem_list':
        return render(request, 'a_common/prime_test/problem_list_content.html', context)

    if request.user.is_authenticated:
        collections = models.ProblemCollection.objects.filter(user=request.user).order_by('order')
    else:
        collections = []

    context = utils.update_context_data(context, collections=collections)
    return render(request, 'a_common/prime_test/problem_list.html', context)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def problem_detail_view(request: utils.HtmxHttpRequest, pk: int):
    config = ProblemConfiguration()
    view_type = request.headers.get('View-Type', '')
    queryset = models.Problem.objects.filter(opened_at__lte=date.today()).order_by('-semester', 'id')
    problem: models.Problem = get_object_or_404(queryset, pk=pk)
    config.url_admin = reverse_lazy(f'admin:a_weekly_problem_change', args=[pk])

    context = utils.update_context_data(config=config, problem_id=pk, problem=problem)

    exam_info = {
        'semester': models.semester_default(), 'circle': problem.circle,
        'subject': problem.subject, 'round': problem.round,
    }
    queryset = queryset.filter(**exam_info)
    prob_prev, prob_next = utils.get_prev_next_prob(pk, queryset)
    student: models.Student = models.Student.objects.filter(user=request.user, **exam_info).first()

    template_nav = 'a_common/prime_test/navigation_container.html'
    template_nav_problem_list = f'{template_nav}#nav_problem_list'
    template_nav_other_list = f'{template_nav}#nav_other_list'

    if view_type == 'problem_list':
        list_data = utils.get_list_data(queryset, student)
        context = utils.update_context_data(context, list_title='', list_data=list_data, color='primary')
        return render(request, template_nav_problem_list, context)

    if view_type == 'like_list':
        queryset = queryset.prefetch_related('likes').filter(
            likes__is_liked=True, likes__user=request.user).annotate(is_liked=F('likes__is_liked'))
        list_data = utils.get_list_data(queryset, student)
        context = utils.update_context_data(context, list_title='즐겨찾기 추가 문제', list_data=list_data, color='danger')
        return render(request, template_nav_other_list, context)

    if view_type == 'rate_list':
        queryset = queryset.prefetch_related('rates').filter(
            rates__isnull=False, rates__user=request.user).annotate(rating=F('rates__rating'))
        list_data = utils.get_list_data(queryset, student)
        context = utils.update_context_data(context, list_title='난이도 선택 문제', list_data=list_data, color='warning')
        return render(request, template_nav_other_list, context)

    if view_type == 'memo_list':
        queryset = queryset.prefetch_related('memos').filter(
            memos__isnull=False, memos__user=request.user)
        list_data = utils.get_list_data(queryset, student)
        context = utils.update_context_data(context, list_title='메모 작성 문제', list_data=list_data, color='warning')
        return render(request, template_nav_other_list, context)

    if view_type == 'tag_list':
        queryset = queryset.prefetch_related('tagged_problems').filter(
            tags__isnull=False, tagged_problems__user=request.user).distinct()
        list_data = utils.get_list_data(queryset, student)
        context = utils.update_context_data(context, list_title='태그 작성 문제', list_data=list_data, color='primary')
        return render(request, template_nav_other_list, context)

    memo_form = forms.ProblemMemoForm()
    custom_data = utils.get_custom_data(request.user, models)
    utils.get_custom_icons(request.user, models, problem, custom_data)

    my_memo = None
    for dt in custom_data['memo']:
        if dt.problem_id == problem.id:
            my_memo = models.ProblemMemo.objects.filter(user=request.user, problem=problem).first()

    tags = []
    for dt in custom_data['tag']:
        if dt.content_object_id == problem.id:
            tags = models.ProblemTag.objects.filter(
                tagged_items__user=request.user,
                tagged_items__content_object=problem,
                tagged_items__active=True,
            ).values_list('name', flat=True)

    context = utils.update_context_data(
        context,
        # icons
        icon_menu=icon_set.ICON_MENU['weekly'],
        icon_question=icon_set.ICON_QUESTION,
        icon_nav=icon_set.ICON_NAV,
        icon_board=icon_set.ICON_BOARD,
        icon_like_white=icon_set.ICON_LIKE['white'],
        icon_rate_white=icon_set.ICON_RATE['white'],
        icon_solve_white=icon_set.ICON_SOLVE['white'],
        icon_memo_white=icon_set.ICON_MEMO['white'],
        icon_tag_white=icon_set.ICON_TAG['white'],

        custom_data=custom_data, my_memo=my_memo, tags=tags,

        # navigation data
        prob_prev=prob_prev, prob_next=prob_next,

        # forms
        memo_form=memo_form,
    )
    return render(request, 'a_common/prime_test/problem_detail.html', context)


@require_POST
@permission_or_staff_required('a_weekly.view_student', login_url='/')
def like_problem(request: utils.HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)
    problem_like, created = models.ProblemLike.objects.get_or_create(user=request.user, problem=problem)
    is_liked = True
    if not created:
        is_liked = not problem_like.is_liked
        problem_like.is_liked = is_liked
        message_type = 'liked' if is_liked else 'unliked'
        problem_like.save(message_type=message_type)
    icon_like = icon_set.ICON_LIKE[f'{is_liked}']
    return HttpResponse(f'{icon_like}')


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def rate_problem(request: utils.HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        problem_rate = models.ProblemRate.objects.filter(user=request.user, problem=problem)
        if problem_rate:
            problem_rate = problem_rate.first()
            problem_rate.rating = rating
            problem_rate.save()
        else:
            models.ProblemRate.objects.create(user=request.user, problem=problem, rating=rating)
        icon_rate = icon_set.ICON_RATE[f'star{rating}']
        return HttpResponse(icon_rate)

    context = utils.update_context_data(problem=problem)
    return render(request, 'a_common/prime_test/rate_modal.html', context)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def memo_problem(request: utils.HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    problem = get_object_or_404(models.Problem, pk=pk)
    instance = models.ProblemMemo.objects.filter(problem=problem, user=request.user).first()
    context = utils.update_context_data(
        problem=problem, icon_memo=icon_set.ICON_MEMO, icon_board=icon_set.ICON_BOARD)

    if view_type == 'create' and request.method == 'POST':
        create_form = forms.ProblemMemoForm(request.POST)
        if create_form.is_valid():
            my_memo = create_form.save(commit=False)
            my_memo.problem_id = pk
            my_memo.user = request.user
            my_memo.save()
            context = utils.update_context_data(context, my_memo=my_memo)
            return render(request, 'a_common/prime_test/memo_container.html', context)

    if view_type == 'update':
        if request.method == 'POST':
            update_form = forms.ProblemMemoForm(request.POST, instance=instance)
            if update_form.is_valid():
                my_memo = update_form.save()
                context = utils.update_context_data(context, my_memo=my_memo)
                return render(request, 'a_common/prime_test/memo_container.html', context)
        else:
            update_base_form = forms.ProblemMemoForm(instance=instance)
            context = utils.update_context_data(context, memo_form=update_base_form, my_memo=instance)
            return render(request, 'a_common/prime_test/memo_update_form.html', context)

    blank_form = forms.ProblemMemoForm()
    context = utils.update_context_data(context, memo_form=blank_form)
    if view_type == 'delete' and request.method == 'POST':
        instance.delete()
        return render(request, 'a_common/prime_test/memo_container.html', context)

    context = utils.update_context_data(context, my_memo=instance)
    return render(request, 'a_common/prime_test/memo_container.html', context)


@require_POST
@permission_or_staff_required('a_weekly.view_student', login_url='/')
def tag_problem(request: utils.HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    problem = get_object_or_404(models.Problem, pk=pk)
    name = request.POST.get('tag', '')

    if view_type == 'add':
        tag, _ = models.ProblemTag.objects.get_or_create(name=name)
        tagged_problem, created = models.ProblemTaggedItem.objects.get_or_create(
            user=request.user, content_object=problem, tag=tag)
        if not created:
            tagged_problem.active = True
            tagged_problem.save(message_type='tagged')

    if view_type == 'remove':
        tagged_problem = get_object_or_404(
            models.ProblemTaggedItem, user=request.user, content_object=problem, tag__name=name)
        tagged_problem.active = False
        tagged_problem.save(message_type='untagged')

    is_tagged = models.ProblemTaggedItem.objects.filter(
        user=request.user, content_object=problem, active=True).exists()
    icon_tag = icon_set.ICON_TAG[f'{is_tagged}']
    html_code = f'<span hx-swap-oob="innerHTML:#weeklyTag{problem.id}">{icon_tag}</span>'
    return HttpResponse(html_code)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def collection_list_view(request: utils.HtmxHttpRequest):
    config = ProblemConfiguration()

    collections = []
    collection_ids = request.POST.getlist('collection')
    if collection_ids:
        for idx, pk in enumerate(collection_ids, start=1):
            collection = models.ProblemCollection.objects.get(pk=pk)
            collection.order = idx
            collection.save()
            collections.append(collection)
    else:
        collections = models.ProblemCollection.objects.filter(user=request.user)
    context = utils.update_context_data(config=config, collections=collections)
    return render(request, 'a_common/prime_test/collection_list.html', context)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def collection_create(request: utils.HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')
    url_create = reverse_lazy('weekly:collection-create')

    if view_type == 'create':
        if request.method == 'POST':
            form = forms.ProblemCollectionForm(request.POST)
            if form.is_valid():
                my_collection = form.save(commit=False)
                existing_collections = models.ProblemCollection.objects.filter(user=request.user)
                max_order = 1
                if existing_collections:
                    max_order = existing_collections.aggregate(max_order=Max('order'))['max_order'] + 1
                my_collection.user = request.user
                my_collection.order = max_order
                my_collection.save()
                return redirect('weekly:collection-list')
        else:
            form = forms.ProblemCollectionForm()
            context = utils.update_context_data(form=form, url=url_create, header='create')
            return render(request, 'a_common/prime_test/collection_create.html', context)

    if view_type == 'create_in_modal':
        if request.method == 'POST':
            problem_id = request.POST.get('problem_id')
            form = forms.ProblemCollectionForm(request.POST)
            if form.is_valid():
                my_collection = form.save(commit=False)
                existing_collections = models.ProblemCollection.objects.filter(user=request.user)
                max_order = 1
                if existing_collections:
                    max_order = existing_collections.aggregate(max_order=Max('order'))['max_order'] + 1
                my_collection.user = request.user
                my_collection.order = max_order
                my_collection.save()
                return redirect('weekly:collect-problem', pk=problem_id)
        else:
            problem_id = request.GET.get('problem_id')
            form = forms.ProblemCollectionForm()
            context = utils.update_context_data(
                form=form, url=url_create, header='create_in_modal',
                problem_id=problem_id, target='#modalContainer')
            return render(request, 'a_common/prime_test/collection_create.html', context)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def collection_detail_view(request: utils.HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    collection = get_object_or_404(models.ProblemCollection, pk=pk)

    if view_type == 'update':
        if request.method == 'POST':
            form = forms.ProblemCollectionForm(request.POST, instance=collection)
            if form.is_valid():
                form.save()
                return redirect('weekly:collection-list')
        else:
            form = forms.ProblemCollectionForm(instance=collection)
            context = utils.update_context_data(form=form, url=collection.get_detail_url(), header='update')
            return render(request, 'a_common/prime_test/collection_create.html', context)

    if view_type == 'delete':
        collection.delete()
        collections = models.ProblemCollection.objects.filter(user_id=request.user.id)
        if collections:
            for idx, col in enumerate(collections, start=1):
                col.order = idx
                col.save()
        return redirect('weekly:collection-list')

    item_ids = request.POST.getlist('item')
    if item_ids:
        for idx, item_pk in enumerate(item_ids, start=1):
            item = models.ProblemCollectionItem.objects.select_related('problem').get(pk=item_pk)
            item.order = idx
            item.save()
    items = models.ProblemCollectionItem.objects.filter(collection=collection)
    custom_data = utils.get_custom_data(request.user, models)
    for item in items:
        utils.get_custom_icons(request.user, models, item.problem, custom_data)
    context = utils.update_context_data(collection=collection, items=items, custom_data=custom_data)
    return render(request, 'a_common/prime_test/collection_item_card.html', context)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def collect_problem(request: utils.HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(models.ProblemCollection, id=collection_id)
        is_checked = request.POST.get('is_checked')

        max_order = models.ProblemCollectionItem.objects.filter(
            collection=collection).aggregate(
            max_order=Coalesce(Max('order'), Value(0)))['max_order'] + 1
        is_collected = False

        if is_checked:
            models.ProblemCollectionItem.objects.create(collection=collection, problem_id=pk, order=max_order)
            is_collected = True
        else:
            item = get_object_or_404(models.ProblemCollectionItem, collection=collection, problem_id=pk)
            item.delete()
            items = models.ProblemCollectionItem.objects.filter(collection=collection)
            if items:
                for idx, it in enumerate(items, start=1):
                    it.order = idx
                    it.save()
        return HttpResponse(icon_set.ICON_COLLECTION[f'{is_collected}'])

    else:
        collection_ids = models.ProblemCollectionItem.objects.filter(
            collection__user_id=request.user.id, problem_id=pk
        ).values_list('collection_id', flat=True).distinct()
        item_exists_case = Case(
            When(id__in=collection_ids, then=1), default=0, output_field=BooleanField())
        collections = models.ProblemCollection.objects.filter(
            user_id=request.user.id).annotate(item_exists=item_exists_case)
        context = utils.update_context_data(problem_id=pk, collections=collections)
        return render(request, 'a_common/prime_test/collection_modal.html', context)
