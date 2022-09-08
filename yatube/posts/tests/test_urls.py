from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.core.cache import cache

from ..models import Group, Post


User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='тестовый текс',
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_author)
        self.authorized_client.force_login(self.user)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_url_exist(self):
        address_list = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.post.author}/',
            f'/posts/{self.post.id}/',
        ]
        for address in address_list:
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exist(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_available_author(self):
        response = self.guest_client.get(f'/profile/{self.post.author}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_redirect_non_auth_user_to_login(self):
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_urls_uses_correct_template(self):
        address_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for address, template in address_url_names.items():
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertTemplateUsed(response, template)
