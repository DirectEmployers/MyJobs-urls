from datetime import datetime
import re

import pytz

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class DestinationManipulation(models.Model):
    """
    Represents the original DestinationManipulation table
    """
    action_type = models.IntegerField()
    buid = models.IntegerField()
    view_source = models.IntegerField()
    action = models.CharField(max_length=255, null=True, default="")
    value_1 = models.TextField(null=True, default="")
    value_2 = models.TextField(null=True, default="")

    class Meta:
        unique_together = ('action_type', 'buid', 'view_source', 'action',
                           'value_1', 'value_2')


class Redirect(models.Model):
    """
    Contains most of the information required to determine how a url
    is to be transformed
    """
    guid = models.CharField(max_length=32, primary_key=True,
                            help_text=_('32-character hex string'))
    buid = models.IntegerField(default=0,
                               help_text=_('Used in conjunction with'
                                           'viewsource_id to index into the '
                                           'RedirectAction table'))
    uid = models.IntegerField(unique=True,
                              help_text=_("Unique id on partner's ATS or "
                                          "other job repository"))
    url = models.TextField(help_text=_('URL being manipulated'))
    new_date = models.DateTimeField(help_text=_('Date that this job was '
                                                'added'))
    expired_date = models.DateTimeField(blank=True, null=True,
                                        help_text=_('Date that this job was'
                                                    'marked as expired'))
    job_location = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    company_name = models.TextField(blank=True)

    def __unicode__(self):
        return u'%s for guid %s' % (self.url, self.guid)


class ATSSourceCode(models.Model):
    """
    Represents one entry in a query string of the form
    ?parameter_name=parameter_value
    """
    buid = models.IntegerField(default=0)
    view_source = models.ForeignKey('ViewSource', blank=False, null=True)
    ats_name = models.CharField(max_length=255)
    parameter_name = models.CharField(max_length=255)
    parameter_value = models.CharField(max_length=255)

    class Meta:
        unique_together = ('ats_name', 'parameter_name', 'parameter_value',
                           'buid', 'view_source')

    def __unicode__(self):
        return u'buid %d, view source %d' % \
            (self.buid, self.view_source_id)


class CanonicalMicrosite(models.Model):
    buid = models.IntegerField(primary_key=True, default=0)
    canonical_microsite_url = models.URLField()

    def __unicode__(self):
        return u'%s for buid %d' % \
            (self.canonical_microsite_url, self.buid)


class RedirectAction(models.Model):
    """
    Determines what transformation(s) should take place based on the provided
    parameters
    """

    # Too manual? To add another action, add it to this list and
    # increment the value in the call to range, then add it to the
    # ACTION_CHOICES tuple
    (SOURCECODETAG_ACTION, MICROSITE_ACTION, MICROSITETAG_ACTION,
        AMPTOAMP_ACTION, CFRAME_ACTION, ANCHORREDIRECTISSUE_ACTION,
        URLSWAP_ACTION, REPLACETHENADD_ACTION, REPLACETHENADDPRE_ACTION,
        SOURCEURLWRAPAPPEND_ACTION, SOURCECODEINSERTION_ACTION,
        SOURCEURLWRAPUNENCODED_ACTION, SOURCEURLWRAPUNENCODEDAPPEND_ACTION,
        SWITCHLASTINSTANCE_ACTION, SWITCHLASTTHENADD_ACTION) = range(15)

    ACTION_CHOICES = (
        (SOURCECODETAG_ACTION, 'sourcecodetag'),
        (MICROSITE_ACTION, 'microsite'),
        (MICROSITETAG_ACTION, 'micrositetag'),
        (AMPTOAMP_ACTION, 'amptoamp'),
        (CFRAME_ACTION, 'cframe'),
        (ANCHORREDIRECTISSUE_ACTION, 'anchorredirectissue'),
        (URLSWAP_ACTION, 'urlswap'),
        (REPLACETHENADD_ACTION, 'replacethenadd'),
        (REPLACETHENADDPRE_ACTION, 'replacethenaddpre'),
        (SOURCEURLWRAPAPPEND_ACTION, 'sourceurlwrapappend'),
        (SOURCECODEINSERTION_ACTION, 'sourcecodeinsertion'),
        (SOURCEURLWRAPUNENCODED_ACTION, 'sourceurlwrapunencoded'),
        (SOURCEURLWRAPUNENCODEDAPPEND_ACTION, 'sourceurlwrapunencodedappend'),
        (SWITCHLASTINSTANCE_ACTION, 'switchlastinstance'),
        (SWITCHLASTTHENADD_ACTION, 'switchlastthenadd'),        
    )

    buid = models.IntegerField(default=0)
    view_source = models.ForeignKey('ViewSource')
    action = models.IntegerField(choices=ACTION_CHOICES,
                                 default=SOURCECODETAG_ACTION)

    class Meta:
        unique_together = ('buid', 'view_source', 'action')
        index_together = [['buid', 'view_source']]

    def __unicode__(self):
        return '%s for buid %d, view source %d' % \
            (self.action, self.buid, self.view_source_id)

    def get_method_name(self):
        return self.ACTION_CHOICES[self.action][1]


class ViewSource(models.Model):
    view_source_id = models.IntegerField(primary_key=True, blank=True,
                                         default=None)
    name = models.CharField(max_length=255)
    friendly_name = models.CharField(max_length=255, blank=True)
    microsite = models.BooleanField(help_text=_('View source is a microsite'))

    class Meta:
        get_latest_by = 'view_source_id'

    def __unicode__(self):
        return u'%s, view source %d' % (self.name, self.view_source_id)

    def save(self, *args, **kwargs):
        if not self.view_source_id:
            # if view_source_id was not provided, set it to the next
            # available value
            try:
                latest = ViewSource.objects.values_list('view_source_id',
                                                        flat=True).latest()
                self.view_source_id = latest + 1
            except ViewSource.DoesNotExist:
                self.view_source_id = 0
        super(ViewSource, self).save(*args, **kwargs)
