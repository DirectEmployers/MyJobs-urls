import sys

from redirect.models import *


def add_query(url, name, value):
    """
    Adds field/value pair to the provided url as a query string

    Appends the proper pair separator (?&) based on the input url

    Inputs:
    :url: URL that query string should be appended to
    :name: Field portion of query string
    :value: Value portion of query string

    Outputs:
    :url: Input url with query string appended
    """
    url += '&' if url.find('?') >= 0 else '?'
    url += '%s=%s' % (name, value)
    return url


def micrositetag(redirect_obj, manipulation_obj):
    """
    Redirects to the given job's entry on the company's microsite,
    or jobs.jobs if one does not exist
    """
    try:
        cm = CanonicalMicrosite.objects.get(buid=redirect_obj.buid)
        microsite_url = cm.canonical_microsite_url
    except CanonicalMicrosite.DoesNotExist:
        microsite_url = 'jobs.jobs/[blank_MS1]/job'
    return microsite_url.replace('[blank_MS1]', str(redirect_obj.uid))


def microsite(redirect_obj, manipulation_obj):
    """
    micrositetag redirect with an additional view source parameter in its
    query string
    """
    url = micrositetag(redirect_obj, manipulation_obj)
    url = url.replace('[Unique_ID]', str(redirect_obj.uid))
    url = add_query(url, 'vs', manipulation_obj.ViewSourceID)
    return url


def sourcecodetag(redirect_obj, manipulation_obj):
    url = redirect_obj.url
    url += '%s' % manipulation_obj.Value1
    return url
