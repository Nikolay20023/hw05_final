from django.shortcuts import render, get_object_or_404
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from .models import Follow, Post, Group, User, Comment
from .utils import paginate_page
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

# Главная страница


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = paginate_page(request, posts)
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            user=request.user.id,
            author=author.id
        ).exists()
    else:
        follow = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': follow
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    form = CommentForm()
    post = get_object_or_404(Post, pk=post_id)
    post_comments = Comment.objects.filter(post=post)
    author = post.author
    context = {
        'post': post,
        'author': author,
        'comments': post_comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template_name = "posts/create_post.html"
    form = PostForm(request.POST, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user.username)
        context = {
            'form': form,
            'is_edit': False
        }
        return render(request, template_name, context)
    context = {
        'form': form,
        'is_edit': False
    }
    return render(request, template_name, {'form': form, 'is_edit': False})


@login_required
def post_edit(request, post_id):
    template_name = "posts/create_post.html"
    post = get_object_or_404(Post, id=post_id)
    if post_id and request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post}
    return render(request, template_name, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/index.html'
    post = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, post)
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author_obj = get_object_or_404(User, username=username)
    user_obj = request.user
    if author_obj != user_obj:
        Follow.objects.get_or_create(
            user=user_obj, author=author_obj
        )
    return redirect(
        'posts:profile',
        username=author_obj.username
    )


@login_required
def profile_unfollow(request, username):
    author_obj = get_object_or_404(User, username=username)
    user_obj = request.user
    follow_qs = Follow.objects.filter(author=author_obj, user=user_obj)
    if follow_qs.exists():
        follow_qs.delete()
    return redirect(
        'posts:profile',
        username=author_obj.username
    )
