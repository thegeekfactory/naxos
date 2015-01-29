from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(
        regex=r'^$',
        view=views.TopView.as_view(),
        name='top'
    ),
    url(
        regex=r'^\+$',
        view=views.NewPost.as_view(),
        name='new_post'
    ),
)