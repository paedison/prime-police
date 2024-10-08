from django.db import models
from django.urls import reverse_lazy
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, TagBase

from a_common.prime_test.model_settings import *
from a_common.models import User


class ProblemTag(BaseProblemTag):
    class Meta(BaseProblemTag.Meta):
        db_table = 'a_weekly_problem_tag'

    def __str__(self):
        return f'[Weekly]ProblemTag(#{self.id}):{self.name}'


class ProblemTaggedItem(BaseProblemTaggedItem):
    tag = models.ForeignKey(ProblemTag, on_delete=models.CASCADE, related_name="tagged_items")
    content_object = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='tagged_problems')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_tagged_items')

    class Meta(BaseProblemTaggedItem.Meta):
        db_table = 'a_weekly_problem_tagged_item'


class Problem(BaseProblem):
    tags = TaggableManager(through=ProblemTaggedItem, blank=True)
    open_users = models.ManyToManyField(User, related_name='weekly_opened_problems', through='ProblemOpen')
    like_users = models.ManyToManyField(User, related_name='weekly_liked_problems', through='ProblemLike')
    rate_users = models.ManyToManyField(User, related_name='weekly_rated_problems', through='ProblemRate')
    solve_users = models.ManyToManyField(User, related_name='weekly_solved_problems', through='ProblemSolve')
    memo_users = models.ManyToManyField(User, related_name='weekly_memoed_problems', through='ProblemMemo')
    collections = models.ManyToManyField(
        'ProblemCollection', related_name='collected_problems', through='ProblemCollectionItem')

    class Meta(BaseProblem.Meta):
        db_table = 'a_weekly_problem'

    def __str__(self):
        return f'[Weekly]Problem(#{self.id}):{self.reference}'

    def get_absolute_url(self):
        return reverse_lazy('weekly:problem-detail', args=[self.id])

    @staticmethod
    def get_list_url():
        return reverse_lazy('weekly:problem-list')

    def get_like_url(self):
        return reverse_lazy('weekly:like-problem', args=[self.id])

    def get_rate_url(self):
        return reverse_lazy('weekly:rate-problem', args=[self.id])

    def get_solve_url(self):
        return reverse_lazy('weekly:solve-problem', args=[self.id])

    def get_memo_url(self):
        return reverse_lazy('weekly:memo-problem', args=[self.id])

    def get_tag_url(self):
        return reverse_lazy('weekly:tag-problem', args=[self.id])

    def get_collect_url(self):
        return reverse_lazy('weekly:collect-problem', args=[self.id])

    def get_admin_change_url(self):
        return reverse_lazy('admin:a_weekly_problem_change', args=[self.id])


class ProblemOpen(BaseProblemOpen):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='opens')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_opens')

    class Meta(BaseProblemOpen.Meta):
        db_table = 'a_weekly_problem_open'

    def __str__(self):
        return f'[Weekly]ProblemOpen(#{self.id}):{self.problem.reference}-{self.user}'


class ProblemLike(BaseProblemLike):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_likes')

    class Meta(BaseProblemLike.Meta):
        db_table = 'a_weekly_problem_like'

    def __str__(self):
        status = 'Liked' if self.is_liked else 'Unliked'
        return f'[Weekly]ProblemLike(#{self.id}):{self.problem.reference}({status})-{self.user}'


class ProblemRate(BaseProblemRate):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='rates')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_rates')

    class Meta(BaseProblemRate.Meta):
        db_table = 'a_weekly_problem_rate'

    def __str__(self):
        return f'[Weekly]ProblemRate(#{self.id}):{self.problem.reference}({self.rating})-{self.user}'


class ProblemSolve(BaseProblemSolve):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solves')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_solves')

    class Meta(BaseProblemSolve.Meta):
        db_table = 'a_weekly_problem_solve'

    def __str__(self):
        status = 'Correct' if self.is_correct else 'Wrong'
        return f'[Weekly]ProblemSolve(#{self.id}):{self.problem.reference}({status})-{self.user}'


class ProblemMemo(BaseProblemMemo):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='memos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_memos')

    class Meta(BaseProblemMemo.Meta):
        db_table = 'a_weekly_problem_memo'

    def __str__(self):
        return f'[Weekly]ProblemMemo(#{self.id}):{self.problem.reference}-{self.user}'


class ProblemCollection(BaseProblemCollection):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_collections')

    class Meta(BaseProblemCollection.Meta):
        db_table = 'a_weekly_problem_collection'

    def __str__(self):
        return f'[Weekly]ProblemCollection(#{self.id}):{self.title}-{self.user}'

    def get_detail_url(self):
        return reverse_lazy('weekly:collection-detail', args=[self.id])


class ProblemCollectionItem(BaseProblemCollectionItem):
    collection = models.ForeignKey(ProblemCollection, on_delete=models.CASCADE, related_name='collected_items')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='collected_problems')

    class Meta(BaseProblemCollectionItem.Meta):
        db_table = 'a_weekly_problem_collection_item'

    def __str__(self):
        return f'[Weekly]ProblemCollectionItem(#{self.id}):{self.collection.title}-{self.problem.reference}'


class Exam(BaseExam):
    class Meta(BaseExam.Meta):
        db_table = 'a_weekly_exam'
        constraints = [
            models.UniqueConstraint(
                fields=['semester', 'circle', 'subject', 'round'],
                name='unique_weekly_exam',
            )
        ]

    def __str__(self):
        return f'[Weekly]Exam:{self.full_reference}'

    @staticmethod
    def get_answer_list_url():
        return reverse_lazy('weekly:answer-list')

    def get_answer_detail_url(self):
        return reverse_lazy('weekly:answer-detail', args=[self.id])

    def get_answer_input_url(self):
        return reverse_lazy('weekly:answer-input', args=[self.id])

    def get_answer_confirm_url(self):
        return reverse_lazy('weekly:answer-confirm', args=[self.id])

    @staticmethod
    def get_staff_menu_url():
        return reverse_lazy('weekly:staff-menu')

    def get_staff_answer_detail_url(self):
        return reverse_lazy('weekly:staff-answer-detail', args=[self.id])

    def get_staff_answer_update_url(self):
        return reverse_lazy('weekly:staff-answer-update', args=[self.id])


class Student(BaseStudent):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_students')

    class Meta(BaseStudent.Meta):
        db_table = 'a_weekly_student'

    def __str__(self):
        return f'[Weekly]Student:{self.user.name}_{self.full_reference}'

    def get_absolute_url(self):
        return reverse_lazy('weekly:answer-detail', args=[self.id])

    def get_rank_verify_url(self):
        return reverse_lazy('weekly:rank-verify', args=[self.id])


class AnswerCount(BaseAnswerCount):
    class Meta(BaseAnswerCount.Meta):
        db_table = 'a_weekly_answer_count'

    def __str__(self):
        return f'[Weekly]AnswerCount:{self.full_reference} {self.number:02}번'
