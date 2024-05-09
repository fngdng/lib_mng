from django.test import TestCase, Client
from django.urls import reverse,resolve
from books.views import history,home,issue,return_item
from books.models import Book, IssuedItem
from django.contrib.auth.models import User

class TestUrls(TestCase):

    def test_history_resolve(self):
        url = reverse('history')
        self.assertEquals(resolve(url).func, history)

    def test_home_resolve(self):
        url = reverse('home')
        self.assertEquals(resolve(url).func, home)

    def test_issue_resolve(self):
        url = reverse('issue')
        self.assertEquals(resolve(url).func, issue)

    def test_return_item_resolve(self):
        url = reverse('return_item')
        self.assertEquals(resolve(url).func, return_item)

class TestViews(TestCase):
    def setUp(self):
        client = Client()
        self.username = 'testuser'
        self.password = 'testpass'
        self.user = User.objects.create_user(
            username=self.username,
            email='testuser@example.com',
            password=self.password,
        )

        self.book = Book.objects.create(
            book_name='Test Book',
            author_name='Test Author',
            quantity=5,
        )

    def test_history_GET(self):
        response = self.client.get(reverse('history'))
        logged_in = self.client.login(
            username=self.username,
            password=self.password,
        )
        self.assertTrue(logged_in)
        response = self.client.get(reverse('history'))
        self.assertEquals(response.status_code,200)
        self.assertTemplateUsed(response,'history.html')

    def test_issue_view_login_required(self):
        url = reverse('issue')
        response = self.client.get(url)
        self.assertRedirects(response, '/login?next=/issue')
        logged_in = self.client.login(
            username=self.username,
            password=self.password,
        )
        self.assertTrue(logged_in)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_issue_view_post(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('issue')
        response = self.client.post(url, {'book_id': self.book.id})
        issued_item = IssuedItem.objects.get(user_id=self.user, book_id=self.book)
        self.assertEqual(issued_item.book_id, self.book)
        self.assertEqual(self.book.quantity, 5)