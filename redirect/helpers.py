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
    url = add_query(url, 'vs', manipulation_obj.view_source)
    return url


def sourcecodetag(redirect_obj, manipulation_obj):
    """
    Appends a query parameter to the redirect url
    """
    url = redirect_obj.url
    url += manipulation_obj.value_1
    return url


def doubleclickwrap(redirect_obj, manipulation_obj):
    """
    Routes url through doubleclick
    """
    return manipulation_obj.value_1 + redirect_obj.url


def doubleclickunwind(redirect_obj, manipulation_obj):
    """
    Removes doubleclick redirect from url
    """
    url = redirect_obj.url.split('?')
    return url[-1]


def anchorredirectissue(redirect_obj, manipulation_obj):
    """
    Removes anchor and adds to query string

    Needs work - query string value is added elsewhere (where?)
    """
    url = redirect_obj.url.split('#')
    return url[0] + manipulation_obj.value_1


def sourcecodeswitch(redirect_obj, manipulation_obj):
    """
    Switches all occurrences of value_1 with value_2

    Works with more than source codes; Current uses: entire urls,
    portions of urls, and source codes
    """
    return redirect_obj.url.replace(manipulation_obj.value_1,
                                    manipulation_obj.value_2)


def sourcecodeinsertion(redirect_obj, manipulation_obj):
    """
    Inserts value_1 into the url immediately before the anchor
    """
    url = redirect_obj.url.split('#')
    url = ('%s#' % manipulation_obj.value_1).join(url)
    return url


def sourceurlwrap(redirect_obj, manipulation_obj):
    """
    Encodes the url and prepends value_1 onto it
    """
    print redirect_obj.url
    url = urllib.quote(redirect_obj.url)
    #url = redirect_obj.url
    return manipulation_obj.value_1 + url


def sourceurlwrapappend(redirect_obj, manipulation_obj):
    """
    sourceurlwrap with value_2 appended
    """
    url = sourceurlwrap(redirect_obj, manipulation_obj)
    return url + manipulation_obj.value_2


def sourceurlwrapunencoded(redirect_obj, manipulation_obj, value1=None):
    """
    Prepends value_1 onto the unencoded url
    """
    value1 = value1 or manipulation_obj.value_1
    return value1 + redirect_obj.url


def sourceurlwrapunencodedappend(redirect_obj, manipulation_obj):
    """
    sourceurlwrapunencoded with value_2 appended
    """
    url = sourceurlwrapunencoded(redirect_obj,
                                 manipulation_obj,
                                 manipulation_obj.value_1)
    return url + manipulation_obj.value_2


def urlswap(redirect_obj, manipulation_obj):
    """
    Swaps the url with value_1
    """
    return manipulation_obj.value_1


def amptoamp(redirect_obj, manipulation_obj):
    """
    Replaces the value before the first ampersand with value_1 and the value
    after the second ampersand with value_2
    """
    url = redirect_obj.url.split('&')
    return redirect_obj.value_1 + url[1] + redirect_obj.value_2


def switchlastinstance(redirect_obj, manipulation_obj, old=None, new=None):
    """
    Replaces the last instance of one value with another

    If called on its own, replaces value_1 with value_2; otherwise replaces
    old with new
    """
    old = value1 or manipulation_obj.value_1
    new = value2 or manipulation_obj.value_2
    return new.join(redirect_obj.url.rsplit(old, 1))


def switchlastthenadd(redirect_obj, manipulation_obj):
    """
    switchlastinstance with value_2 appended

    The old and new values are '!!!!'-delimited and are stored in value_1
    """
    old, new = manipulation_obj.value_1.split('!!!!')
    new_url = switchlastinstance(redirect_obj, manipulation_obj, old, new)
    return new_url + manipulation_obj.value_2


def replace(redirect_obj, manipulation_obj):
    """
    Utility function that is used in the replacethenadd* actions
    """
    old, new = manipulation_obj.value_1.split('!!!!')
    return redirect_obj.url.replace(old, new)


def replacethenadd(redirect_obj, manipulation_obj):
    """
    Replaces all instances of one value with another, then appends value_2

    The values are '!!!!'-delimited and are stored in value_1
    """
    url = replace(redirect_obj, manipulation_obj)
    return url + manipulation_obj.value_2


def replacethenaddpre(redirect_obj, manipulation_obj):
    """
    Replaces all instances of one value with another, then prepends value_2

    The values are '!!!!'-delimited and are stored in value_1
    """
    url = replace(redirect_obj, manipulation_obj)
    return manipulation_obj.value_2 + url

def cframe(redirect_obj, manipulation_obj):
    """
    Redirects to the company frame denoted by value_1, appending the job url
    as the url query parameter
    """
    url = urllib.urlencode(redirect_obj.url)
    url = '%s?url=%s' % (manipulation_obj.value_1, url)
    return 'http://directemployers.us.jobs/companyframe/' + url
