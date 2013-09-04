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


def micrositetag(redirect_obj, view_source):
    """
    Redirects to the given job's entry on the company's microsite,
    or jobs.jobs if one does not exist
    """
    try:
        cm = CanonicalMicrosite.objects.get(buid=redirect_obj.buid)
        microsite_url = cm.canonical_microsite_url
    except CanonicalMicrosite.DoesNotExist:
        microsite_url = 'jobs.jobs/%s/job'
    return microsite_url % redirect_obj.uid


def microsite(redirect_obj, view_source):
    """
    micrositetag redirect with an additional view source parameter in its
    query string
    """
    url = micrositetag(redirect_obj, view_source)
    url = add_query(url, 'vs', view_source.pk)
    return url


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
