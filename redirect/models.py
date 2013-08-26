from datetime import datetime
import re

import pytz

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class CanonicalMicrosite(models.Model):
    buid = models.IntegerField()
    canonical_microsite_url = models.URLField()


class Redirect(models.Model):
    guid = models.CharField(max_length=32, unique=True)
    buid = models.ForeignKey(CanonicalMicrosite)
    url = models.URLField()
    new_date = models.DateTimeField()
    expired_date = models.DateTimeField(blank=True, null=True)


class ViewSource(models.Model):
    viewsource_id = models.IntegerField(primary_key=True, default=0)
    name = models.CharField(max_length=255)
    microsite = models.BooleanField()

    class Meta:
        get_latest_by = 'viewsource_id'

    def save(self, *args, **kwargs):
        if not self.viewsource_id:
            try:
                latest = ViewSource.objects.values_list('viewsource_id',
                                                        flat=True).latest()
                self.viewsource_id = latest + 1
            except ViewSource.DoesNotExist:
                self.viewsource_id = 0
        super(ViewSource, self).save(*args, **kwargs)


class RedirectAction(models.Model):
    buid = models.ForeignKey(CanonicalMicrosite)
    view_source = models.ForeignKey(ViewSource)
    action = models.CharField(max_length=255)


class ATSSourceCode(models.Model):
    ats_name = models.CharField(max_length=255)
    parameter_name = models.CharField(max_length=255)
    parameter_value = models.CharField(max_length=255)
