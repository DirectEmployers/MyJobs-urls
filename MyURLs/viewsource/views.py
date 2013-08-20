import json
import uuid

from django.http import HttpResponse
from django.shortcuts import redirect

from viewsource.models import ViewSource


def home(request, guid, vsid='0'):
    guid = uuid.UUID(guid)
    return_val = {'guid': str(guid), 'vsid': vsid}

    return HttpResponse(json.dumps(return_val))
