import pytest
from django.urls import reverse
from http import HTTPStatus
from django.contrib.auth.models import User
from news.models import News, Comment


@pytest.fixture
def create_user(db):
    return User.objects.create_user(username="user", password="password")


@pytest.fixture
def create_news(db):
    return News.objects.create(title="Test News", text="Some news content")


@pytest.fixture
def create_comment(db, create_user, create_news):
    return Comment.objects.create(
        news=create_news, author=create_user, text="Test comment")


@pytest.mark.django_db
def test_homepage_accessible(client):
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_detail_page_accessible(client, create_news):
    url = reverse('news:detail', args=[create_news.pk])
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_comment_delete_accessible_by_author(client, create_comment):
    client.login(username="user", password="password")
    url = reverse('news:delete', args=[create_comment.pk])
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_comment_edit_accessible_by_author(client, create_comment):
    client.login(username="user", password="password")
    url = reverse('news:edit', args=[create_comment.pk])
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_redirect_anonymous_user_to_login(client, create_comment):
    delete_url = reverse('news:delete', args=[create_comment.pk])
    edit_url = reverse('news:edit', args=[create_comment.pk])
    login_url = reverse('users:login')

    delete_response = client.get(delete_url)
    assert delete_response.status_code == HTTPStatus.FOUND
    assert delete_response.url == f"{login_url}?next={delete_url}"

    edit_response = client.get(edit_url)
    assert edit_response.status_code == HTTPStatus.FOUND
    assert edit_response.url == f"{login_url}?next={edit_url}"


@pytest.mark.django_db
def test_other_user_cannot_access_edit_or_delete(client, create_comment):
    User.objects.create_user(
        username="other_user", password="password")
    client.login(username="other_user", password="password")

    delete_url = reverse('news:delete', args=[create_comment.pk])
    edit_url = reverse('news:edit', args=[create_comment.pk])

    delete_response = client.get(delete_url)
    assert delete_response.status_code == HTTPStatus.NOT_FOUND

    edit_response = client.get(edit_url)
    assert edit_response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_auth_pages_accessible(client):
    login_url = reverse('users:login')
    logout_url = reverse('users:logout')
    signup_url = reverse('users:signup')

    assert client.get(login_url).status_code == HTTPStatus.OK
    assert client.get(logout_url).status_code == HTTPStatus.OK
    assert client.get(signup_url).status_code == HTTPStatus.OK
