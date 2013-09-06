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
        viewsource = models.ViewSource.objects.get(view_source_id=vsid)
    except models.ViewSource.DoesNotExist:
        data['type'] = 'no_vsid'
        return HttpResponse(json.dumps(data))

    try:
        ra = models.RedirectAction.objects.get(buid=guid_redirect.buid,
                                               view_source=viewsource)
    except models.RedirectAction.DoesNotExist:
        data['type'] = 'no_redirect_action'
        return HttpResponse(json.dumps(data))

    method_name = ra.get_method_name()

    try:
        redirect_method = getattr(helpers, method_name)
        data['type'] = method_name
    except AttributeError:
        data['type'] = 'method_not_defined'

    redirect_url = redirect_method(guid_redirect, viewsource)
    data['url'] = redirect_url

    return HttpResponse(json.dumps(data))
