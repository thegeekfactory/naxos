from django.conf.urls import url

from . import views


app_name = 'blog'
urlpatterns = [
    url(
        regex=r'^$',
        view=views.TopView.as_view(),
        name='top'
    ),
    url(
        regex=r'^(?P<slug>[\w|\-]+)$',
        view=views.PostView.as_view(),
        name='post'
    ),
    url(
        regex=r'^\+$',
        view=views.NewPost.as_view(),
        name='new_post'
    ),
    url(
        regex=r'^edit=(?P<slug>[\w|\-]+)$',
        view=views.EditPost.as_view(),
        name='edit'
    ),
]
