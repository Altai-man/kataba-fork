# coding: utf-8
from django.contrib import admin
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin

from board.models import *
#from board.forms import *



class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', 'activation_code')}),
        (_('Permissions'), {'fields': ('is_active', 'is_admin', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )

    list_display = ('email', 'is_admin')
    list_filter = ('is_admin', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    form = UserChangeForm
    add_form = UserCreationForm
    add_form_template = 'add_form.html'

admin.site.register(User, UserAdmin)