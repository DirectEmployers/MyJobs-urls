import json
import uuid

from django.http import Http404, HttpResponse, HttpResponseRedirect
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
        manipulation = models.DestinationManipulation.objects.get(
            buid=guid_redirect.buid, view_source=vsid, action_type=1)
    except models.DestinationManipulation.DoesNotExist:
        try:
            manipulation = models.DestinationManipulation.objects.get(
                buid=guid_redirect.buid, view_source=0, action_type=1)
        except models.DestinationManipulation.DoesNotExist:
            raise Http404

    method_name = manipulation.action

    try:
        redirect_method = getattr(helpers, method_name)
        data['type'] = method_name
    except AttributeError:
        data['type'] = 'method_not_defined'

    redirect_url = redirect_method(guid_redirect, manipulation)
    data['url'] = redirect_url
    
    #return HttpResponse(redirect_url)
    #return HttpResponse(json.dumps(data))
    return HttpResponseRedirect(redirect_url)
