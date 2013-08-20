from django.db import models
from django.utils.translation import ugettext_lazy as _


class ViewSource(models.Model):
    name = models.CharField(max_length=255)
    # Django doesn't allow multiple AutoFields
    # viewsource_id is a normal int field that is manipulated in save()
    viewsource_id = models.IntegerField(unique=True, blank=True)
    partner_name = models.CharField(max_length=255)
    partner_url = models.URLField(max_length=300)
    source_code = models.CharField(max_length=300, blank=True)
    redirect_url = models.URLField(max_length=300, blank=True)

    class Meta:
        get_latest_by = 'viewsource_id'
        unique_together = (('viewsource_id', 'partner_name'),)

    def save(self, *args, **kwargs):
        if not self.viewsource_id:
            try:
                latest = ViewSource.objects.values_list('viewsource_id',
                                                        flat=True).latest()
                self.viewsource_id = latest + 1
            except ViewSource.DoesNotExist:
                self.viewsource_id = 0
        super(ViewSource, self).save(*args, **kwargs)
