import json
import uuid

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from redirect import models


def home(request, guid, vsid='0'):
    guid_redirect = get_object_or_404(models.Redirect, guid=guid)
    try:
        vs = models.ViewSource.objects.get(viewsource_id=vsid)
        vsid = vs.viewsource_id
    except models.ViewSource.DoesNotExist:
        vsid = 0
    return_val = {'guid': guid_redirect.guid, 'vsid': vsid}

    return HttpResponse(json.dumps(return_val))
