import json
import uuid

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from redirect import models


def home(request, guid, vsid='0'):
    guid_redirect = get_object_or_404(models.Redirect, guid=guid)
    viewsource = get_object_or_404(models.ViewSource, view_source_id=vsid)
    return_val = {'guid': guid_redirect.guid,
                  'vsid': viewsource.view_source_id}

    return HttpResponse(json.dumps(return_val))
