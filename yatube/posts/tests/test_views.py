import shutil
import tempfile

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..forms import PostForm
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


from ..models import Group, Post, Follow


User = get_user_model()


class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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

        cls.user = User.objects.create_user(username='Name1')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id='1',
            image=uploaded,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_namespaces_urls_matching(self):

        templtates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': PostsPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTests.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': PostsPagesTests.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for reverse_name, template in templtates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):

        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['posts'][0].text,
                         PostsPagesTests.post.text)
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_group_list_correct_context(self):

        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PostsPagesTests.group.slug}
        ))
        self.assertEqual(response.context['group'].title,
                         PostsPagesTests.group.title)
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_profile_correct_context(self):

        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': PostsPagesTests.user.username}
        ))
        self.assertEqual(response.context['author_posts'][0].author,
                         PostsPagesTests.user)
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_post_detail_correct_context(self):

        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsPagesTests.post.id}
        ))
        self.assertEqual(response.context['post_id'],
                         int(PostsPagesTests.post.id))
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_post_edit_correct_context(self):

        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PostsPagesTests.post.id}
        ))
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['post_id'], PostsPagesTests.post.id)

    def test_create_correct_context(self):

        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PostsPagesTests.post.id}
        ))
        self.assertIsInstance(response.context['form'], PostForm)

    def test_cache_index(self):

        response = self.client.get(reverse('posts:index'))
        post1 = response.content
        del_post = Post.objects.filter(id=2)
        del_post.delete()
        response = self.client.get(reverse('posts:index'))
        post2 = response.content
        self.assertEqual(post1, post2)


class PaginatorViewsTest(TestCase):
    '''Тестирование работы паджинатора.'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='name1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост №{i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='username')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        urls = {
            reverse('posts:index'): 'index',
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug}): 'group',
            reverse('posts:profile',
                    kwargs={
                        'username': PaginatorViewsTest.author.username
                    }): 'profile',
        }
        for url in urls.keys():
            response = self.client.get(url)
            self.assertEqual(len(response.context.get('page_obj').object_list),
                             10)

    def test_second_page_contains_three_posts(self):
        urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_list', kwargs={
                'slug': PaginatorViewsTest.group.slug
            }) + '?page=2':
            'group',
            reverse('posts:profile',
                    kwargs={
                        'username': PaginatorViewsTest.author.username
                    }) + '?page=2':
            'profile',
        }
        for url in urls.keys():
            response = self.client.get(url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 3
            )


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовый пост'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_following.username}
                    )
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(
            'profile/{FollowTests.user_following.username}/follow/'
        )
        self.client_auth_follower.get(
            'profile/{FollowTests.user_following.username}/unfollow/'
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get(
            '/follow/'
        )
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, self.post.text)
        response = self.client_auth_following.get(
            '/follow/'
        )
        self.assertNotContains(response, self.post.text)
