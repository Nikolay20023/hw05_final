from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def test_models_correct_objects_name(self):
        group = PostModelTest.group
        excepted_object_name = group.title
        self.assertEqual(excepted_object_name, str(group))

    def models_correct_objects_text(self):
        post = PostModelTest.post
        excepted_object_name = post.text[:15]
        self.assertEqual(excepted_object_name, str(post))
