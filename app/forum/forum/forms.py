from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit, Button
from crispy_forms.bootstrap import InlineRadios

import datetime

from .models import Post, PollQuestion, PollChoice
from .util import normalize_query

toolbar = "{% include \"toolbar.html\" %}"  # Text format


class GenericThreadForm(forms.ModelForm):

    CHOICES = ((str(i + 1), 'icon{:d}.gif'.format(i + 1)) for i in range(16))
    title = forms.CharField(max_length=140, label='Titre')
    icon = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=CHOICES, label="Icône"
    )
    personal = forms.BooleanField(
        label=("Sujet personnel : permet la suppression du sujet."),
        required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['icon'].initial = 1

    def clean_icon(self):
        return "icon" + self.cleaned_data['icon'] + ".gif"

    class Meta:
        model = Post
        fields = ('title', 'icon', 'content_plain', 'personal')


# Basic thread stuff
class ThreadForm(GenericThreadForm):
    """Create and/or edit Thread & Posts: .views.NewThread & EditPost"""

    def __init__(self, *args, **kwargs):
        c_slug = kwargs.pop('category_slug')
        # If editing an existing thread
        try:
            thread = kwargs.pop('thread')
            post = kwargs.pop('post')
            new = False
        except:
            new = True
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Publier', accesskey="s"))
        self.helper.add_input(Submit('preview', 'Prévisualiser',))
        if new:  # This is a new thread
            self.helper.form_action = reverse(
                'forum:new_thread', kwargs={'category_slug': c_slug})
            self.helper.layout = Layout(Field('title'),
                                        InlineRadios('icon'),
                                        HTML(toolbar),
                                        Field('content_plain'),
                                        Field('personal'))
        else:  # This is an edit - used by .views.EditPost
            if post == thread.posts.first():
                self.helper.layout = Layout(Field('title'),
                                            InlineRadios('icon'),
                                            HTML(toolbar),
                                            Field('content_plain'),
                                            Field('personal', type='hidden'))
                self.helper.add_input(Button('cession',
                                             'Céder le contrôle',
                                             css_class='btn-default',
                                             data_toggle='modal',
                                             data_target='#cessionModal'))
                if thread.personal:
                    self.helper.add_input(Button('delete',
                                                 'Supprimer',
                                                 css_class='btn-default',
                                                 data_toggle='modal',
                                                 data_target='#deleteModal'))
            else:  # If it's not the first post
                self.fields['title'].required = False
                self.fields['icon'].required = False
                self.helper.layout = Layout(Field('title', disabled=''),
                                            HTML(toolbar),
                                            Field('content_plain'),
                                            Field('icon', type='hidden'),
                                            Field('personal', type='hidden'))
            self.helper.form_action = reverse(
                'forum:edit', kwargs={'category_slug': c_slug,
                                      'thread_slug': thread.slug,
                                      'pk': post.pk})


class PostForm(forms.ModelForm):
    """PostForm as used by .views.NewPost"""
    title = forms.CharField(max_length=140, label='Titre', required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.c_slug = kwargs.pop('category_slug')
        self.t = kwargs.pop('thread')
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'forum:new_post', kwargs={'category_slug': self.c_slug,
                                      'thread_slug': self.t.slug})
        self.helper.layout = Layout(
            Field('title', value=self.t.title, disabled=''),
            HTML(toolbar),
            Field('content_plain'))
        self.helper.add_input(Submit('submit', 'Répondre', accesskey="s"))
        self.helper.add_input(Submit('preview', 'Prévisualiser',))

    def clean(self):
        if ((timezone.now() - self.user.posts.latest().created) <
                datetime.timedelta(seconds=5)):
            raise forms.ValidationError("Merci d'attendre au moins 5 secondes"
                                        " entre deux messages.")

    class Meta:
        model = Post
        fields = ('content_plain',)


# Polls stuff
class PollThreadForm(GenericThreadForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(Field('title'),
                                    InlineRadios('icon'),
                                    HTML(toolbar),
                                    Field('content_plain'))
        self.helper.form_tag = False


class QuestionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model = PollQuestion
        fields = ('question_text',)
        labels = {'question_text': 'Question'}


class FormSetHelper(FormHelper):

    """Enables crispy forms for ChoicesFormSet"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False


class CustomCleanFormset(BaseInlineFormSet):

    def clean(self):
        super().clean()
        choices = list()
        for form in self.forms:
            try:
                choice_text = normalize_query(
                    form.cleaned_data['choice_text'])
            except:
                continue  # Skip empty choice fields
            if choice_text in choices:
                msg = "Chaque choix doit être unique."
                raise forms.ValidationError(msg)
            else:
                choices.append(choice_text)


ChoicesFormSet = inlineformset_factory(
    PollQuestion,
    PollChoice,
    formset=CustomCleanFormset,
    fields=('choice_text',),
    labels={'choice_text': 'Choix'},
    can_delete=False,
    extra=10,
    min_num=2,
    max_num=10
)
