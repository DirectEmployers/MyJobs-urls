from redirect.models import *


def add_query(url, name, value):
    url += '&' if url.find('?') >= 0 else '?'
    url += '%s=%s' % (name, value)
    return url

def micrositetag(redirect_obj, view_source):
    try:
        cm = CanonicalMicrosite.objects.get(buid=redirect_obj.buid)
        microsite_url = cm.canonical_microsite_url
    except CanonicalMicrosite.DoesNotExist:
        microsite_url = 'jobs.jobs/%s/job'
    return microsite_url % redirect_obj.uid

def passthrough(redirect_obj, view_source):
    return redirect_obj.url

def sourcecodetag(redirect_obj, view_source):
    url = redirect_obj.url
    try:
        source_code = ATSSourceCode.objects.get(buid=redirect_obj.buid,
                                                view_source=view_source)
        url = add_query(url,
                        source_code.parameter_name,
                        source_code.parameter_value)
    except ATSSourceCode.DoesNotExist:
        pass
    return url

def microsite(redirect_obj, view_source):
    url = micrositetag(redirect_obj, view_source)
    url = add_query(url, 'vs', view_source.pk)
    return url
