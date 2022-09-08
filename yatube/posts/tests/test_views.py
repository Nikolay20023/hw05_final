from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group

User = get_user_model()


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='тестовый текс',
            author=cls.user_author,
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='StasBasov')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.author_post = Client()
        self.author_post.force_login(self.post.author)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_pages_correct_template(self):
        templates_pages_name = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={
                    'slug': self.group.slug
                }): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.post.author
            }): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id
            }): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id
            }): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_post.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
            self.assertEqual(post.author, PostPagesTest.user_author)
            self.assertEqual(post.pub_date, PostPagesTest.post.pub_date)
            self.assertEqual(post.text, PostPagesTest.post.text)
            self.assertEqual(post.group, PostPagesTest.group)
            self.assertEqual(post.image, PostPagesTest.post.image)

    def test_index_page_show_correct_context(self):
        response = self.auth_client.get(reverse('posts:index'))
        self.check_context_contains_page_or_post(response.context)

    def test_group_post_page_show_correct_context(self):
        response = self.auth_client.get(reverse('posts:group_posts', kwargs={
            'slug': self.group.slug
        }))
        self.check_context_contains_page_or_post(response.context)
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_profile_page_show_correct_context(self):
        response = self.auth_client.get(reverse('posts:profile', kwargs={
            'username': self.post.author
        }))
        self.check_context_contains_page_or_post(response.context)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user_author)

    def test_post_edit_page_show_correct_context(self):
        template_pages_name = {
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id
            }): True,
            reverse('posts:post_create'): False
        }
        for url, bool in template_pages_name.items():
            with self.subTest(url=url):
                response = self.author_post.get(url)
                self.assertIn('form', response.context)
                self.assertEqual(response.context['is_edit'], bool)

    def test_post_detail_page_show_correct_context(self):
        response = self.author_post.get(reverse('posts:post_detail', kwargs={
            'post_id': self.post.id
        }))
        self.check_context_contains_page_or_post(response.context, post=True)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['post'].image, self.post.image)
        self.assertEqual(response.context['author'], self.user_author)

    def test_casche(self):
        response = self.auth_client.get(reverse('posts:index'))
        count_objects = len(response.context['page_obj'])
        self.assertTrue(count_objects > 0)
        post = Post.objects.all()
        post.delete()
        self.assertTrue(Post.objects.count, 0)
        response = self.auth_client.get(reverse('posts:index'))
        self.assertTrue(response.context is None)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user('author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='text',
            author=cls.user,
            group=cls.group
        )
        cls.paginator_amount = 10
        cls.second_amount = 3

        posts = [
            Post(
                text=f'text{num}',
                author=cls.user,
                group=cls.group
            ) for num in range(1, cls.paginator_amount + cls.second_amount)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self) -> None:
        self.client_user = Client()

    def test_first_page_(self):
        paginator_amount = 10
        second_amount = 3
        pages = (
            (1, paginator_amount),
            (2, second_amount)
        )
        template_pages_name = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts', kwargs={
                    'slug': self.group.slug
                }),
            reverse('posts:profile', kwargs={
                'username': self.post.author
            }),
        ]
        for name in template_pages_name:
            for page, cnt in pages:
                with self.subTest(page=page):
                    response = self.client_user.get(
                        name,
                        {'page': page}
                    )
                    self.assertEqual(
                        len(response.context.get('page_obj').object_list), cnt
                    )
