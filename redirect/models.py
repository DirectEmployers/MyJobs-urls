from datetime import datetime
import re

import pytz

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Redirect(models.Model):
    """
    Contains most of the information required to determine how a url
    is to be transformed
    """
    guid = models.CharField(max_length=32, unique=True,
                            help_text=_('32-character hex string'))
    buid = models.IntegerField(default=0)
    uid = models.IntegerField(unique=True)
    url = models.URLField(help_text=_('URL being manipulated'))
    new_date = models.DateTimeField(help_text=_('Date that this job was '
                                                'added'))
    expired_date = models.DateTimeField(blank=True, null=True,
                                        help_text=_('Date that this job was'
                                                    'marked as expired'))


class ATSSourceCode(models.Model):
    """
    Represents one entry in a query string of the form
    ?parameter_name=parameter_value
    """
    ats_name = models.CharField(max_length=255)
    parameter_name = models.CharField(max_length=255)
    parameter_value = models.CharField(max_length=255)


class CanonicalMicrosite(models.Model):
    buid = models.IntegerField()
    canonical_microsite_url = models.URLField()


class RedirectAction(models.Model):
    """
    Determines what transformation(s) should take place based on the provided
    parameters
    """
    buid = models.IntegerField(default=0)
    view_source = models.ForeignKey('ViewSource')
    action = models.CharField(max_length=255)


class ViewSource(models.Model):
    viewsource_id = models.IntegerField(primary_key=True, default=0)
    name = models.CharField(max_length=255)
    microsite = models.BooleanField()

    class Meta:
        get_latest_by = 'viewsource_id'

    def save(self, *args, **kwargs):
        if not self.viewsource_id:
            # if viewsource_id was not provided, set it to the next
            # available value
            try:
                latest = ViewSource.objects.values_list('viewsource_id',
                                                        flat=True).latest()
                self.viewsource_id = latest + 1
            except ViewSource.DoesNotExist:
                self.viewsource_id = 0
        super(ViewSource, self).save(*args, **kwargs)
