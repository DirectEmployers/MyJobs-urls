import json
import uuid

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from redirect import models
from redirect import helpers


def home(request, guid, vsid='0'):
    guid_redirect = get_object_or_404(models.Redirect, guid=guid)
    try:
        viewsource = models.ViewSource.objects.get(view_source_id=vsid)
    except models.ViewSource.DoesNotExist:
        # passthrough redirect
        return HttpResponse(json.dumps({'guid': guid_redirect.guid,
                                        'vsid': vsid,
                                        'type': 'passthrough',
                                        'url': guid_redirect.url}))

    ra = models.RedirectAction.objects.get(buid=guid_redirect.buid,
                                           view_source=viewsource)
    method_name = models.RedirectAction.ACTION_CHOICES[ra.action][1]

    redirect_method = getattr(helpers, method_name)
    redirect_url = redirect_method(guid_redirect, viewsource)

    return_val = {'guid': guid_redirect.guid,
                  'vsid': viewsource.view_source_id,
                  'url': redirect_url}

    return HttpResponse(json.dumps(return_val))
