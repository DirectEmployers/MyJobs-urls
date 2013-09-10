import json
import uuid

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from redirect import models
from redirect import helpers


def home(request, guid, vsid='0'):
    guid_redirect = get_object_or_404(models.Redirect, guid=guid)
    data = {'guid': guid_redirect.guid,
            'vsid': vsid,
            'type': '',
            'url': guid_redirect.url}

    try:
        manipulation = models.Destination_Manipulation.objects.get(
            BUID=guid_redirect.buid, ViewSourceID=vsid, ActionType=1)
    except models.Destination_Manipulation.DoesNotExist:
        try:
            manipulation = models.Destination_Manipulation.objects.get(
                BUID=guid_redirect.buid, ViewSourceID=0, ActionType=1)
        except models.Destination_Manipulation.DoesNotExist:
            raise Http404

    method_name = manipulation.Action

    try:
        redirect_method = getattr(helpers, method_name)
        data['type'] = method_name
    except AttributeError:
        data['type'] = 'method_not_defined'

    redirect_url = redirect_method(guid_redirect, manipulation)
    data['url'] = redirect_url

    return HttpResponse(json.dumps(data))
