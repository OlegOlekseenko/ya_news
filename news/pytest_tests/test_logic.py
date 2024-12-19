import pytest
from django.urls import reverse
from news.models import News, Comment
from news.forms import BAD_WORDS, WARNING


@pytest.fixture
def create_news(db):
    return News.objects.create(title="News Title", text="News Content")


@pytest.fixture
def create_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="user", password="password")


@pytest.fixture
def create_comment(db, create_news, create_user):
    return Comment.objects.create(
        news=create_news, author=create_user, text="Valid comment")


@pytest.mark.django_db
def test_anonymous_user_cant_post_comment(client, create_news):
    url = reverse('news:detail', args=[create_news.pk])
    response = client.post(url, data={'text': 'Anonymous comment'})
    assert Comment.objects.count() == 0
    assert response.status_code == 302  # Redirect to login


@pytest.mark.django_db
def test_authorized_user_can_post_comment(client, create_news, create_user):
    client.login(username="user", password="password")
    url = reverse('news:detail', args=[create_news.pk])
    response = client.post(url, data={'text': 'Authorized comment'})
    assert Comment.objects.count() == 1
    comment = Comment.objects.first()
    assert comment.text == 'Authorized comment'
    assert response.status_code == 302  # Redirect after successful post


@pytest.mark.django_db
def test_bad_words_in_comment(client, create_news, create_user):
    client.login(username="user", password="password")
    url = reverse('news:detail', args=[create_news.pk])
    response = client.post(
        url, data={'text': f"This is a {BAD_WORDS[0]} comment"})
    assert Comment.objects.count() == 0
    assert WARNING in response.context['form'].errors['text']


@pytest.mark.django_db
def test_author_can_edit_comment(client, create_comment):
    client.login(username=create_comment.author.username, password="password")
    url = reverse('news:edit', args=[create_comment.pk])
    response = client.post(url, data={'text': 'Updated comment'})
    create_comment.refresh_from_db()
    assert create_comment.text == 'Updated comment'
    assert response.status_code == 302


@pytest.mark.django_db
def test_author_can_delete_comment(client, create_comment):
    client.login(username=create_comment.author.username, password="password")
    url = reverse('news:delete', args=[create_comment.pk])
    response = client.post(url)
    assert Comment.objects.count() == 0
    assert response.status_code == 302


@pytest.mark.django_db
def test_user_cant_edit_others_comment(
    client, create_comment, django_user_model
):
    django_user_model.objects.create_user(
        username="other_user", password="password")
    client.login(username="other_user", password="password")
    url = reverse('news:edit', args=[create_comment.pk])
    response = client.post(url, data={'text': 'Unauthorized update'})
    create_comment.refresh_from_db()
    assert create_comment.text != 'Unauthorized update'
    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cant_delete_others_comment(
    client, create_comment, django_user_model
):
    django_user_model.objects.create_user(
        username="other_user", password="password")
    client.login(username="other_user", password="password")
    url = reverse('news:delete', args=[create_comment.pk])
    response = client.post(url)
    assert Comment.objects.count() == 1
    assert response.status_code == 404
