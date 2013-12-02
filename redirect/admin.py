from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import Group

from redirect.models import *


class ViewSourceAdmin(admin.ModelAdmin):
    """
    Currently unused, but will be used once the improved models are in place.
    """
    def get_readonly_fields(self, request, obj=None):
        """
        If a new object is being created, leave view_source_id editable.
        If the user is viewing an existing object, make it read-only.
        """
        if obj:
            return self.readonly_fields + ('view_source_id',)
        else:
            return []


class DestinationManipulationAdmin(admin.ModelAdmin):
    list_filter = ['action_type', 'action']
    search_fields = ['=buid']
    list_display = ['buid', 'view_source', 'action_type', 'action', 'value_1', 'value_2']


class RedirectAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = super(RedirectAdmin, self).queryset(request)
        return qs.filter(expired_date=None)


admin.site.register(Redirect, RedirectAdmin)
admin.site.register(DestinationManipulation, DestinationManipulationAdmin)
