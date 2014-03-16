#! -*- coding: utf-8 -*-
# Python
import os
from PIL import Image
import re

# Django
from django.db import models
from django import forms
from captcha.fields import CaptchaField
from django.conf import settings
from django.utils.html import escape
from django.db.models.signals import pre_delete, post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db.models.signals import post_save
from django.contrib.auth.forms import ReadOnlyPasswordHashField


ALREADY_ACTIVATED = 'ALREADY_ACTIVATED'


class Board(models.Model):
    name = models.CharField(max_length=4)
    pages = models.IntegerField(default=30)
    thread_max_post = models.IntegerField(default=500)

    def get_cloud_view(self):
        # Threads. ("th" 'cause it is shorter)
        threads = Thread.objects.filter(board_id=self).order_by('-update_time')
        
        # How many values should be.
        count = len(threads) + 3 - len(threads) % 3
        
        # Giving back final array
        f = lambda x,y: y[x] if x < len(y) else []
        return [[f(k,threads) for k in xrange(i,i+3)] for i in xrange(0,count,3)]

    def get_board_view(self):
        threads = Thread.objects.filter(board_id=self).order_by('-update_time')
        return [dict(thread=th, posts=th.latest_posts()) for th in threads]
    
    def __unicode__(self):
        return ''.join(['/',self.name,'/'])
        
class SearchManager(models.Manager):
    def search(self,search_text, search_place, board):
        # Making search text safe
        search_text = escape(search_text)
        
        # Where should we search?
        if (search_place == 'topic'):
            query = self.filter(topic__icontains=search_text)
        elif (search_place == 'text'):
            query = self.filter(text__icontains=search_text)
        elif (search_place == 'both'):
            query = self.filter(models.Q(topic__icontains=search_text) | models.Q(text__icontains=search_text))
        
        return query

        
class BasePostModel(models.Model):
    name = models.CharField(max_length=14, default=u'Anonymous')
    text = models.TextField(max_length=8000)
    topic = models.CharField(max_length=40)
    date = models.DateTimeField('%Y-%m-%d %H:%M:%S', auto_now_add=True)
    image = models.ImageField(upload_to='.')
    
    # Link to board
    board_id = models.ForeignKey('board')
    
    # Custom Manager
    objects = SearchManager()

    # Delete image and it's thumbnail
    def delete_images(self):
        if self.image:
            images = [''.join([settings.MEDIA_ROOT,'/',self.image.name]),
                      ''.join([settings.MEDIA_ROOT,'/thumbnails',self.image.name])]
            for image in images:
                if os.path.isfile(image):
                    os.remove(image)    
            

    def make_thumbnail(self):
        """Method which makes thumbnail. Surprise?"""
        if self.image:
            ratio = min(settings.PIC_SIZE/self.image.height,settings.PIC_SIZE/self.image.width)
            thumbnail = Image.open(self.image.path)
            thumbnail.thumbnail((int(self.image.width*ratio),int(self.image.height*ratio)),Image.ANTIALIAS)
            thumbnail.save(''.join([settings.MEDIA_ROOT,'/thumbnails/',self.image.name]),thumbnail.format)
            return True
        else:
            return False
        
    @staticmethod
    def markup(string):
        """ Makes markup for post and thread text. Strings will be safe. """
        string = escape(string)
        markups = [
            # quote
            [r'(?P<text>(?<!(&gt;))&gt;(?!(&gt;)).+)', r'<span class="quote">\g<text></span>'], 
            
            # bold **b**
            [r'\*\*(?P<text>[^*%]+)\*\*' ,r'<b>\g<text></b>'], 
            
            # cursive *i*
            [r'\*(?P<text>[^*%]+)\*', r'<i>\g<text></i>'],
            
            #spoiler %%s%%
            [r'\%\%(?P<text>[^*%]+)\%\%',r'<span class="spoiler">\g<text></span>'],
            
            # link to thread >t14
            [r'\&gt;\&gt;t(?P<id>[0-9]+)',
            r'<div class="link_to_content"><a class="link_to_post" href="/thread/\g<id>">&gt;&gt;t\g<id></a><div class="post_quote"></div></div>'],
            
            # link to post >p88
            [r'\&gt;\&gt;p(?P<id>[0-9]+)',
            r'<div class="link_to_content"><a class="link_to_post" href="/post/\g<id>">&gt;&gt;p\g<id></a><div class="post_quote"></div></div>'], 
            
            # new line
            [r'\n',r'<br>'], 
        ]
        for one_markup in markups:
            string = re.sub(one_markup[0], one_markup[1], string)
        return string
        
    def __unicode__(self):
        return ''.join([self.topic,': ',self.text[:40],', ',str(self.date)])
    
    class Meta:
        abstract = True

class Thread(BasePostModel):
    # Removing old threads
    @classmethod
    def remove_old_threads(cls, board):
        threads_to_delete = cls.objects.filter(board_id=board).order_by('-update_time')[board.pages*settings.THREADS:]
        for th in threads_to_delete:
            th.delete()
    
    def save(self,*args, **kwargs):
        super(Thread,self).save(*args, **kwargs)
        # No more old threads!
        self.remove_old_threads(self.board_id)

    def latest_posts(self,count=3):
        posts = reversed(Post.objects.filter(thread_id=self).order_by('-id')[:count]) # 9,8,7
        return posts

    post_count = models.IntegerField(default=0)
    update_time = models.DateTimeField('%Y-%m-%d %H:%M:%S', auto_now_add=True)

class Post(BasePostModel):        
    thread_id = models.ForeignKey('thread') 
    sage = models.BooleanField(default=False)

class ThreadForm(forms.ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Thread
        fields = ['topic','text','image']

class PostForm(forms.ModelForm):
    # captcha = CaptchaField()
    def __init__(self, *args, **kwargs):
        super(PostForm,self).__init__(*args, **kwargs)
        # Images and sage are not required for posts
        self.fields['image'].required = False
        self.fields['sage'].required = False
	self.fields['topic'].required = False
        
    class Meta:
        model = Post
        fields = ['name','topic','sage','text','image']



class UserManager(BaseUserManager):
    """
    Creates and saves a User with the given email and password.
    """
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        customer = self.model(
            email=UserManager.normalize_email(email),
        )
        customer.set_password(password)
        customer.save(using=self._db)
        return customer

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        customer = self.create_user(email, password)
        customer.is_admin = True
        customer.save(using=self._db)
        return customer


class User(AbstractBaseUser, PermissionsMixin):
    """
    A model which implements the authentication model.

    Password are required. Other fields are optional.
    """
    email = models.EmailField(
        _('Email'), max_length=255, unique=True)

    is_admin = models.BooleanField(_('Admin status'), default=False)
    is_active = models.BooleanField(_('Active'), default=True)

    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)
    activation_code = models.CharField(_('Activation code'), max_length=255)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def get_short_name(self):
        return "User"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label=_('Password'),
        help_text=_('Raw passwords are not stored, so there is no way to see '
                    'this user\'s password, but you can change the password '
                    'using <a href="password/">this form</a>.'))

    class Meta:
        model = User

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

    def clean_password(self):
        return self.initial['password']


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """
    error_messages = {
        'duplicate_epmail': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = User
        fields = ('email', 'password',)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])


    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        customer = super(UserCreationForm, self).save(commit=False)
        customer.set_password(self.cleaned_data["password1"])
        if commit:
            customer.save()
        return customer


# Signals

# Use callback to delete images ('cause CASCADE does not call .delete())
@receiver(pre_delete, sender=Thread)
@receiver(pre_delete, sender=Post)
def pre_delete_callback(sender, instance, **kwargs):
    instance.delete_images()

# Callbacks here because save does not always mean new object
@receiver(pre_save, sender=Post)
@receiver(pre_save, sender=Thread)
def pre_save_callback(sender, instance, **kwargs):
    # is it update for something or new object? If it is new, id is None
    if instance.id is None:
        # Topic must be safe
        instance.topic = escape(instance.topic)
        
        # Markup
        instance.text = instance.markup(instance.text)


@receiver(post_save, sender=Thread)
@receiver(post_save, sender=Post)
def post_save_callback(sender, instance, **kwargs):
    if kwargs['created']:
        # Thumbnail
        instance.make_thumbnail()