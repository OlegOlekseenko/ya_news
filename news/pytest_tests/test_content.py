import pytest
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from news.models import News, Comment
from news.forms import CommentForm


@pytest.fixture
def create_news_list(db):
    today = timezone.now()
    news_list = [
        News(
            title=f"News {i}",
            text="Some content",
            date=today - timezone.timedelta(days=i),
        )
        for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(news_list)


@pytest.fixture
def create_news_with_comments(db, django_user_model):
    user = django_user_model.objects.create_user(
        username="commenter", password="password")
    news = News.objects.create(title="News with comments", text="Content")
    comments = [
        Comment(
            news=news, author=user,
            text=f"Comment {i}",
            created=timezone.now() + timezone.timedelta(minutes=i))
        for i in range(5)
    ]
    Comment.objects.bulk_create(comments)
    return news


@pytest.mark.django_db
def test_news_count_on_homepage(client, create_news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order_on_homepage(client, create_news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    dates = [news.date for news in object_list]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.django_db
def test_comments_order_on_detail_page(client, create_news_with_comments):
    url = reverse('news:detail', args=[create_news_with_comments.pk])
    response = client.get(url)
    news = response.context['news']
    comments = news.comment_set.all()
    timestamps = [comment.created for comment in comments]
    assert timestamps == sorted(timestamps)


@pytest.mark.django_db
def test_comment_form_for_anonymous_user(client, create_news_with_comments):
    url = reverse('news:detail', args=[create_news_with_comments.pk])
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_comment_form_for_authorized_user(
    client, django_user_model, create_news_with_comments
):
    django_user_model.objects.create_user(
        username="user", password="password")
    client.login(username="user", password="password")
    url = reverse('news:detail', args=[create_news_with_comments.pk])
    response = client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
