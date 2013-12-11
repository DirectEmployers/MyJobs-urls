from django.contrib import admin
from django.contrib.auth.models import Group

from redirect.models import *


class ViewSourceAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('view_source_id',)
        else:
            return []


class ExcludedViewSourceAdmin(admin.ModelAdmin):
    list_display = ['view_source']


admin.site.register(Redirect)
admin.site.register(DestinationManipulation)
admin.site.register(ATSSourceCode)
admin.site.register(ViewSource, ViewSourceAdmin)
admin.site.register(RedirectAction)
admin.site.register(CanonicalMicrosite)
admin.site.register(ExcludedViewSource, ExcludedViewSourceAdmin)
