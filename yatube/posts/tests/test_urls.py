from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Group, Post


User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Name1')
        cls.user2 = User.objects.create_user(username='Name2')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Trapatapatau'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_2 = Client()

        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user2)

    def test_url_uses_correct_index(self):
        '''Главная страница доступна любому пользователю.'''
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    # def test_about_author(self):
    #     response = self.guest_client.get('/about/author/')
    #     self.assertEqual(response.status_code, 200)

    # def test_about_tech(self):
    #     response = self.guest_client.get('/about/tech/')
    #     self.assertEqual(response.status_code, 200)

    def test_pages_for_unauthorized(self):
        '''Страницы - главная, группы, поста, профиля, об авторе, о технологиях -
           доступны любому пользователю.'''
        available_urls = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': StaticURLTests.group.slug}),
            reverse('posts:post_detail',
                    kwargs={'post_id': StaticURLTests.post.id}),
            reverse('posts:profile',
                    kwargs={'username': StaticURLTests.user.username}),
            reverse('about:author'),
            reverse('about:tech')
        ]
        for url in available_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_not_available_pages_for_unauthorized(self):
        '''Страница создания, редактирования и комментирования поста
           недоступна неавторизованному пользователю.'''

        not_available_urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': StaticURLTests.post.id}),
            reverse('posts:add_comment',
                    kwargs={'post_id': StaticURLTests.post.id})
        ]
        for url in not_available_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_edit_url_not_by_author(self):
        '''Страница редактирования поста недоступна не автору поста.'''
        response = self.authorized_client_2.get(
            f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_error_404(self):
        '''Несуществующая страница возвращает ошибку 404
           и обрабатывается кастомным шаблоном.'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template(self):
        '''Страницы приложений posts и about используют корректные шаблоны.'''
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{StaticURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{StaticURLTests.user}/': 'posts/profile.html',
            f'/posts/{StaticURLTests.post.id}/edit/': 'posts/create_post.html',
            f'/posts/{StaticURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
