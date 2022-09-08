from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment, Follow


User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой относится пост',
            'image': 'Связанная картинка',
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if data.lower() == '':
            raise forms.ValidationError('Вы должны заполнить поля текста ')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_text = {
            'text': 'Текст нового комментария'
        }


class FollowForm(forms.ModelForm):
    model = Follow
    fields = ('user', 'author',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if data.lower() == '':
            raise forms.ValidationError('Вы должны заполнить поля текста ')
        return data
    '''def clean_slug(self):
        """Обрабатывает случай, если slug не уникален."""
        cleaned_data = super().clean()
        slug = cleaned_data.get('slug')
        if not slug:
            title = cleaned_data.get('title')
            slug = slugify(title)[:100]
        if Post.objects.filter(slug=slug).exists():
            raise forms.ValidationError(
                f'Адрес "{slug}" уже существует, '
                'придумайте уникальное значение'
            )
        return slug'''
