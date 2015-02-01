from django.db import models
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime
from uuslug import uuslug

from .util import convert_text_to_html, smilify, keygen
from user.models import ForumUser

SLUG_LENGTH = 50


### Abstract models ###
class CachedAuthorModel(models.Model):
    """Gets author from cache else from db and create cache"""

    @property
    def cached_author(self):
        author = cache.get('user/{}'.format(self.author_id))
        if not author:
            author = ForumUser.objects.get(pk=self.author_id)
            cache.set('user/{}'.format(self.author_id), author, None)
        return author

    class Meta:
        abstract = True


### Basic Forum models ###
class Category(models.Model):
    """Contains threads."""
    slug = models.SlugField(blank=False, unique=True, db_index=True)
    title = models.CharField(max_length=50, blank=False)
    subtitle = models.CharField(max_length=200)
    postCount = models.IntegerField(default=0)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.slug


class Thread(CachedAuthorModel):
    """Contains posts."""
    slug = models.SlugField(max_length=SLUG_LENGTH)
    title = models.CharField(max_length=80, verbose_name='Titre')
    author = models.ForeignKey(ForumUser, related_name='threads')
    contributors = models.ManyToManyField(ForumUser)
    category = models.ForeignKey(Category, related_name='threads')
    icon = models.CharField(
        max_length=80, default="icon1.gif", verbose_name='Icône')
    isSticky = models.BooleanField(default=False)
    isLocked = models.BooleanField(default=False)
    isRemoved = models.BooleanField(default=False)
    viewCount = models.IntegerField(default=0)
    modified = models.DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        """Custom save to create a slug from title"""
        self.slug = uuslug(self.title,
                           filter_dict={'category': self.category},
                           instance=self,
                           max_length=SLUG_LENGTH)
        if not self.slug:  # Prevent empty strings as slug
            self.slug = uuslug('sans titre',
                               filter_dict={'category': self.category},
                               instance=self,
                               max_length=SLUG_LENGTH)
        super().save(*args, **kwargs)

    @property
    def latest_post(self):
        latest_post = cache.get('thread/{}/latest_post'.format(self.pk))
        if not latest_post:
            latest_post = self.posts.latest()
            cache.set(
                'thread/{}/latest_post'.format(self.pk), latest_post, None)
        return latest_post

    @property
    def post_count(self):
        post_count = cache.get('thread/{}/post_count'.format(self.pk))
        if not post_count:
            post_count = self.posts.count()
            cache.set(
                'thread/{}/post_count'.format(self.pk), post_count, None)
        return post_count

    class Meta:
        ordering = ["-isSticky", "-modified", "pk"]
        index_together = ['category', 'slug']
        # Permit category.threads.latest in template
        get_latest_by = "modified"

    def __str__(self):
        return "{}/{}".format(self.category.slug, self.slug)


class Post(CachedAuthorModel):
    """A post."""
    created = models.DateTimeField(default=datetime.now,
                                   editable=False)
    modified = models.DateTimeField(blank=True, null=True)
    content_plain = models.TextField(verbose_name='Message')
    markup = models.TextField(default='bbcode')
    author = models.ForeignKey(ForumUser, related_name='posts')
    thread = models.ForeignKey(Thread, related_name='posts')

    def save(self, *args, **kwargs):
        new_post = True if self.pk is None else False
        self.thread.contributors.add(self.author)
        if self.pk is None:
            self.thread.modified = self.created
            self.thread.save()
        super().save(*args, **kwargs)

    @property
    def html(self):
        html = cache.get('post/{}/html'.format(self.pk))
        if not html:
            html = convert_text_to_html(self.content_plain, self.markup)
            html = smilify(html)
            cache.set('post/{}/html'.format(self.pk), html, None)
        return html
    
    @property
    def position(self):
        return Post.objects.filter(thread=self.thread).filter(
                                   pk__lt=self.pk).count()

    class Meta:
        ordering = ["pk"]
        # Permit thread.posts.latest in template
        get_latest_by = "created"

    def __str__(self):
        return "{:s}: {:d}".format(self.author.username, self.pk)


class Preview(models.Model):
    """Contains post previews. Should be empty."""
    content_plain = models.TextField()
    content_html = models.TextField()

    def save(self, *args, **kwargs):
        self.content_html = convert_text_to_html(self.content_plain)
        self.content_html = smilify(self.content_html)
        super().save(*args, **kwargs)

    def __str__(self):
        return "{:d}".format(self.pk)


class ThreadCession(models.Model):
    thread = models.OneToOneField(Thread)
    token = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        queryset = self.__class__.objects.all()
        self.token = keygen()
        while queryset.filter(token=self.token).exists():
            self.token = keygen()
        super().save(*args, **kwargs)

    def __str__(self):
        return thread


### Poll models ###
class PollQuestion(models.Model):
    question_text = models.CharField(max_length=80)
    thread = models.OneToOneField(Thread, related_name='question')
    voters = models.ManyToManyField(ForumUser, blank=True)

    def __str__(self):
        return self.question_text


class PollChoice(models.Model):
    question = models.ForeignKey(PollQuestion, related_name='choices')
    choice_text = models.CharField(max_length=40)
    votes = models.IntegerField(default=0)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.choice_text


### Model signal handlers ###
@receiver(post_save, sender=Post)
def update_post_cache(created, instance, **kwargs):
    """Update cached data when a post is saved"""
    html = convert_text_to_html(instance.content_plain, instance.markup)
    html = smilify(html)
    cache.set("post/{}/html".format(instance.pk), html, None)
    if created:
        cache.set("thread/{}/contributors".format(instance.thread.pk),
                  instance.thread.contributors.all(), None)
        cache.set('thread/{}/post_count'.format(instance.thread.pk),
                  instance.thread.posts.count(), None)
