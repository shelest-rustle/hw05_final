from django.contrib.auth import get_user_model
from django.test import TestCase


from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает метод __str__."""
        act = str(PostModelTest.post)
        self.assertEqual(
            act, PostModelTest.post.text[:15],
            'Метод __str__ модели Post работает неправильно'
        )
        act = str(PostModelTest.group)
        self.assertEqual(
            act, PostModelTest.group.title,
            'Метод __str__ модели Group работает неправильно'
        )
