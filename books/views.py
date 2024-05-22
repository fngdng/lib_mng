from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from .models import Book, IssuedItem
from django.contrib import messages
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from django.core.paginator import Paginator
from django import forms


class ActionDispatchView(View):
    action = None

    def dispatch(self, request, *args, **kwargs):
        if self.action:
            handler = getattr(self, self.action, self.http_method_not_allowed)
            return handler(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)


class IssueForm(forms.Form):
    book_id = forms.IntegerField(widget=forms.HiddenInput)


class ReturnForm(forms.Form):
    book_id = forms.IntegerField(widget=forms.HiddenInput)


class LibraryManagementView(ActionDispatchView):
    action_methods = {
        'home': 'home',
        'login': 'login',
        'register': 'register',
        'logout': 'logout',
        'issue': 'issue',
        'return_item': 'return_item',
        'history': 'history',
    }

    def get(self, request, *args, **kwargs):
        action = kwargs.get('action')
        handler_name = self.action_methods.get(action, 'home')
        handler = getattr(self, handler_name)
        return handler(request)

    def post(self, request, *args, **kwargs):
        action = kwargs.get('action')
        handler_name = self.action_methods.get(action)
        if handler_name:
            handler = getattr(self, handler_name)
            return handler(request)
        return redirect('home')

    def home(self, request):
        return render(request, 'home.html')

    def login(self, request):
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(username=username, password=password)
                if user is not None:
                    auth_login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid Credentials')
        else:
            form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def register(self, request):
        if request.method == 'POST':
            form = RegisterForm(request.POST)
            if form.is_valid():
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                username = form.cleaned_data['username']
                email = form.cleaned_data['email']
                password1 = form.cleaned_data['password1']
                password2 = form.cleaned_data['password2']
                if password1 != password2:
                    messages.error(request, 'Passwords do not match')
                elif User.objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists')
                elif User.objects.filter(email=email).exists():
                    messages.error(request, 'Email already registered')
                else:
                    User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password1)
                    messages.success(request, 'Registration successful')
                    return redirect('login')
        else:
            form = RegisterForm()
        return render(request, 'register.html', {'form': form})

    def logout(self, request):
        auth_logout(request)
        return redirect('home')

    @method_decorator(csrf_exempt)
    def issue(self, request):
        if request.method == 'POST':
            form = IssueForm(request.POST)
            if form.is_valid():
                book_id = form.cleaned_data['book_id']
                current_book = Book.objects.get(id=book_id)
                if current_book.quantity == 0:
                    messages.error(request, 'Book not available')
                else:
                    current_book.quantity -= 1
                    current_book.save()
                    IssuedItem.objects.create(user_id=request.user, book_id=current_book)
                    messages.success(request, 'Book issued successfully')
        else:
            form = IssueForm()
        my_items = IssuedItem.objects.filter(user_id=request.user, return_date__isnull=True).values_list('book_id', flat=True)
        books = Book.objects.exclude(id__in=my_items).filter(quantity__gt=0)
        return render(request, 'issue_item.html', {'form': form, 'books': books})

    @method_decorator(csrf_exempt)
    def return_item(self, request):
        if request.method == 'POST':
            form = ReturnForm(request.POST)
            if form.is_valid():
                book_id = form.cleaned_data['book_id']
                current_book = Book.objects.get(id=book_id)
                current_book.quantity += 1
                current_book.save()
                issue_item = IssuedItem.objects.filter(user_id=request.user, book_id=current_book, return_date__isnull=True).first()
                if issue_item:
                    issue_item.return_date = date.today()
                    issue_item.save()
                    messages.success(request, 'Book returned successfully')
        else:
            form = ReturnForm()
        my_items = IssuedItem.objects.filter(user_id=request.user, return_date__isnull=True).values_list('book_id', flat=True)
        books = Book.objects.filter(id__in=my_items)
        return render(request, 'return_item.html', {'form': form, 'books': books})

    def history(self, request):
        my_items = IssuedItem.objects.filter(user_id=request.user).order_by('-issue_date')
        paginator = Paginator(my_items, 10)
        page_number = request.GET.get('page')
        show_data_final = paginator.get_page(page_number)
        return render(request, 'history.html', {'books': show_data_final})
