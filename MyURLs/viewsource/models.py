from datetime import datetime

import pytz

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class ViewSource(models.Model):
    name = models.CharField(max_length=255)
    # Django doesn't allow multiple AutoFields
    # viewsource_id is a normal int field that is manipulated in save()
    viewsource_id = models.IntegerField(blank=True)
    buid = models.IntegerField(default=0)
    partner_name = models.CharField(max_length=255)
    partner_url = models.URLField(max_length=300)
    source_code = models.CharField(max_length=300, blank=True)
    redirect_url = models.URLField(max_length=300, blank=True)
    # date_new should be in another app?
    date_new = models.DateTimeField(default=datetime.now)

    class Meta:
        get_latest_by = 'viewsource_id'
        unique_together = (('viewsource_id', 'buid'),)
        index_together = [['viewsource_id', 'buid'],]

    def save(self, *args, **kwargs):
        if not self.viewsource_id:
            try:
                latest = ViewSource.objects.values_list('viewsource_id',
                                                        flat=True).latest()
                self.viewsource_id = latest + 1
            except ViewSource.DoesNotExist:
                self.viewsource_id = 0
        super(ViewSource, self).save(*args, **kwargs)

    def get_url(self, guid):
        if self.date_new + settings.LANDING_DELAY > datetime.now(tz=pytz.utc):
            # job may not have been propagated to microsites
            # bypass normal rules
            return self.redirect_url
        else:
            # job has been propagated
            # transform url as normal
            return self.transform_url(guid)

    def transform_url(self, guid):
        raise NotImplementedError('transform to final url')