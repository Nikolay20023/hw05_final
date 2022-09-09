from http import HTTPStatus
import shutil
import tempfile

from ..models import Post, Group, Comment
from ..forms import PostForm
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Описание',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.guest_client.force_login(self.user)
        self.anauthorized_client = Client()

    def test_detail_post(self):
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group
        )
        new_post_text = 'dsdsdsada'
        group_today = Group.objects.create(
            title='Тестовый загоdsловок',
            slug='test_slug_1',
            description='Описанsdие',
        )
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': post.id
            }),
            data={'text': new_post_text, 'group': group_today.id},
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.text, new_post_text)
        self.assertEqual(post.group, group_today)

    def test_comment_on_post_page(self):
        comment_count = Comment.objects.count()
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group
        )
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={
                        'post_id': post.id
                    }
                    ),
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={
                'post_id': post.id
            })
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Тестовый комментарий')
        self.assertEqual(comment.author, self.user)

    def test_comment_unathor_page(self):
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group
        )
        response = self.anauthorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': post.id
            })
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{post.id}/comment/'
        )

    def test_create_post(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data={
                'text': 'Test_post',
                'group': self.group.id,
                'image': uploaded
            },
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        post_2 = Post.objects.first()
        self.assertEqual(post_2.text, 'Test_post')
        self.assertEqual(post_2.author, self.user)
        self.assertEqual(post_2.group, self.group)
        self.assertIn(uploaded.name, post_2.image.name)

    def test_auth_user_cant_publish_post(self):
        response = self.anauthorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Test_post', 'group': self.group.id},
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), 0)
