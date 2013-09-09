import sys
import urllib

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


def doubleclickwrap(redirect_obj, manipulation_obj):
    return manipulation_obj.Value1 + redirect_obj.url


def doubleclickunwind(redirect_obj, manipulation_obj):
    url = redirect_obj.url.split('?')
    return url[0]


def anchorredirectissue(redirect_obj, manipulation_obj):
    url = redirect_obj.url.split('#')
    return url[0]


def sourcecodeswitch(redirect_obj, manipulation_obj):
    return redirect_obj.url.replace(manipulation_obj.Value1,
                                    manipulation_obj.Value2)


def sourcecodeinsertion(redirect_obj, manipulation_obj):
    url = redirect_obj.url.split('#')
    url = ('%s#' % manipulation_obj.Value1).join(url)
    return url


def sourceurlwrap(redirect_obj, manipulation_obj):
    url = urllib.urlencode(redirect_obj.url)
    return manipulation_obj.Value1 + url


def sourceurlwrapappend(redirect_obj, manipulation_obj):
    url = urllib.urlencode(redirect_obj.url)
    return manipulation_obj.Value1 + url + manipulation_obj.Value2


def sourceurlwrapunencoded(redirect_obj, manipulation_obj, value1=None):
    value1 = value1 or manipulation_obj.Value1
    return value1 + redirect_obj.url
    return manipulation_obj.Value1 + redirect_obj.url


def sourceurlwrapunencodedappend(redirect_obj, manipulation_obj):
    url = sourceurlwrapunencoded(redirect_obj,
                                 manipulation_obj,
                                 manipulation_obj.Value1)
    return url + manipulation_obj.Value2


def urlswap(redirect_obj, manipulation_obj):
    return manipulation_obj.Value1


def amptoamp(redirect_obj, manipulation_obj):
    url = redirect_obj.url.split('&')
    return redirect_obj.Value1 + url[0] + redirect_obj.Value2


def switchlastinstance(redirect_obj, manipulation_obj, old=None, new=None):
    old = value1 or manipulation_obj.Value1
    new = value2 or manipulation_obj.Value2
    return new.join(redirect_obj.url.rsplit(old, 1))


def switchlastthenadd(redirect_obj, manipulation_obj):
    old, new = manipulation_obj.Value1.split('!!!!')
    new_url = switchlastinstance(redirect_obj, manipulation_obj, old, new)
    return new_url + manipulation_obj.Value2


def replace(redirect_obj, manipulation_obj):
    """
    Utility function that is used in the `replacethenadd*` actions
    """
    old, new = manipulation_obj.Value1.split('!!!!')
    return redirect_obj.url.replace(old, new)


def replacethenadd(redirect_obj, manipulation_obj):
    url = replace(redirect_obj, manipulation_obj)
    return url + manipulation_obj.Value2


def replacethenaddpre(redirect_obj, manipulation_obj):
    url = replace(redirect_obj, manipulation_obj)
    return manipulation_obj.Value2 + url

def cframe(redirect_obj, manipulation_obj):
    url = urllib.urlencode(redirect_obj.url)
    url = '%s?url=%s' % (manipulation_obj.Value1, url)
    return 'http://directemployers.us.jobs/companyframe/' + url
