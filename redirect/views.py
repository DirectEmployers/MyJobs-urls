import json
import urllib
import uuid

from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect

from redirect import models
from redirect import helpers


def home(request, guid, vsid='0'):
    guid_redirect = get_object_or_404(models.Redirect, guid=uuid.UUID(guid))

    try:
        manipulation = models.DestinationManipulation.objects.get(
            buid=guid_redirect.buid, view_source=vsid, action_type=1)        
    except models.DestinationManipulation.DoesNotExist:
        try:
            manipulation = models.DestinationManipulation.objects.get(
                buid=guid_redirect.buid, view_source=vsid)
        except models.DestinationManipulation.DoesNotExist:
            raise Http404

    if manipulation.view_source == 1604:
        # msccn redirect
        company_name = guid_redirect.company_name
        company_name = helpers.quote_string(company_name)
        redirect_url = 'http://us.jobs/msccn-referral.asp?gi=%s%s&cp=%s&u=%s' % \
                       (guid_redirect.guid,
                       manipulation.view_source,
                       company_name,
                       guid_redirect.uid)
    elif manipulation.view_source == 294:
        # facebook redirect
        redirect_url = 'http://apps.facebook.com/us-jobs/?jvid=%s%s' % \
            (guid_redirect.guid, manipulation.view_source)
    else:
        method_name = manipulation.action

        try:
            redirect_method = getattr(helpers, method_name)
        except AttributeError:
            pass

        print guid
        print vsid
        redirect_url = redirect_method(guid_redirect, manipulation)

    return HttpResponsePermanentRedirect(redirect_url)
