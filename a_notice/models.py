from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse

from a_common.models import User


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자 ID", db_column="user_id")
    title = models.CharField("제목", max_length=50)
    content = RichTextUploadingField()
    hit = models.IntegerField("조회수", default=1)
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)
    top_fixed = models.BooleanField("상단 고정", default=False)
    is_hidden = models.BooleanField("비밀글", default=False)

    class Meta:
        verbose_name = verbose_name_plural = "공지사항"
        ordering = ["-id"]

    def __str__(self):
        return f'[Notice]Post(#{self.id}):{self.title}'

    @property
    def comment_count(self):
        return self.post_comments.count()

    def get_absolute_url(self):
        return reverse(f'notice:detail', args=[self.id])

    @staticmethod
    def get_list_url():
        return reverse(f'notice:base')

    def get_create_url(self):
        return reverse(f'notice:create', args=[self.id])

    def get_update_url(self):
        return reverse(f'notice:update', args=[self.id])

    def get_delete_url(self):
        return reverse(f'notice:delete', args=[self.id])

    def get_comment_create_url(self):
        return reverse(f'notice:comment_create', args=[self.id])

    def update_hit(self):
        hit = self.hit
        self.hit = hit + 1
        self.save()


class Comment(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="사용자 ID",
        db_column="user_id", related_name="user_comments")
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, verbose_name="게시글",
        db_column="post_id", related_name="post_comments")
    content = models.TextField("내용")
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "댓글"
        ordering = ["-id"]

    def __str__(self):
        return f'[Notice]Comment(#{self.id}):{self.user.username}-{self.post.title}'

    def get_update_url(self):
        return reverse(f'notice:comment_update', args=[self.id])

    def get_delete_url(self):
        return reverse(f'notice:comment_delete', args=[self.id])

    def get_post_detail_url(self):
        return reverse(f'notice:detail', args=[self.post.id])
