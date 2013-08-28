from django.contrib import admin
from django.contrib.auth.models import Group

from redirect.models import *

admin.site.register(Redirect)
admin.site.register(ATSSourceCode)
admin.site.register(ViewSource)
admin.site.register(RedirectAction)
admin.site.register(CanonicalMicrosite)
