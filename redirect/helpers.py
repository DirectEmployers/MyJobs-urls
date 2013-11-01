from django.utils.http import urlquote_plus

from redirect.models import *


"""

Utility methods and constants

"""

STATE_MAP = {
    'ct-': {'buid': 2656,
            'site': 'connecticut.us.jobs'},
    'ms-': {'buid': 2674,
            'site': 'mississippi.us.jobs'},
    'nj-': {'buid': 2680,
            'site': 'newjersey.us.jobs'},
    'nv-': {'buid': 2678,
            'site': 'nevada.us.jobs'},
    'ny-': {'buid': 2682,
            'site': 'newyork.us.jobs'},
    'pr-': {'buid': 2701,
            'site': 'puertorico.us.jobs'},
    'gu-': {'buid': 2703,
            'site': 'guam.us.jobs'},
}


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


def get_hosted_state_url(redirect, url):
    """
    Transforms us.jobs links into branded us.jobs links, if branding exists
    for the provided job's location.

    Inputs:
    :redirect: Redirect instance dictated by the guid used in the initial
        request
    :url: URL to be transformed
    """
    if redirect.buid == 1228:
        state_str = redirect.job_location[:3].lower()
        new_ms = STATE_MAP.get(state_str, {}).get('site', 'us.jobs')
        url = url.replace('us.jobs', new_ms)
    return url


def get_Post_a_Job_buid(redirect):
    """
    Returns the state-specific buid for a given job's location, if one exists.

    Used during logging only.

    Inputs:
    :redirect: Redirect object associated with a given guid

    Outputs:
    :buid: State-specific buid, if one exists
    """
    buid = redirect.buid
    if buid == 1228:
        state_str = redirect.job_location[:3].lower()
        buid = STATE_MAP.get(state_str, {}).get('buid', buid)
    return buid


def quote_string(value):
    """
    Due to differences between VBScript and Python %% encoding, certain
    substitutions must be done manually. These are required in multiple
    circumstances.

    TODO: Do these encoding issues actually harm anything? Can we get away
    with not manually replacing punctuation that is perfectly valid?

    Inputs:
    :value: String to be quoted

    :value: Quoted string
    """
    value = urlquote_plus(value, safe='')
    value = value.replace('.', '%2E')
    value = value.replace('-', '%2D')
    value = value.replace('_', '%5F')
    return value


"""

URL manipulation methods

"""


def micrositetag(redirect_obj, manipulation_obj):
    """
    Redirects to the url from redirect_obj.url with source codes appended.
    """
    url = redirect_obj.url.replace('[Unique_ID]', str(redirect_obj.uid))

    # There is often (always?) a second action that needs to take place
    # to achieve the correct manipulated result.
    try:
        # Try to retrieve a DestinationManipulation object for the current
        # buid and view_source, but for action_type 2
        manipulation_2 = DestinationManipulation.objects.get(
            buid=manipulation_obj.buid,
            view_source=manipulation_obj.view_source,
            action_type=2)
    except DestinationManipulation.DoesNotExist:
        try:
            # If the previous does not exist, check view_source 0
            manipulation_2 = DestinationManipulation.objects.get(
                buid=redirect_obj.buid, view_source=0, action_type=2)
        except DestinationManipulation.DoesNotExist:
            manipulation_2 = None

    if manipulation_2 and (manipulation_2.value_1 != '[blank]'):
        # A manipulation exists. Retrieve the method corresponding to its
        # action, call that method, and return the result
        method_name = manipulation_2.action
        method = globals()[method_name]
        redirect_obj.url = url
        url = method(redirect_obj, manipulation_2)

    return url


def microsite(redirect_obj, manipulation_obj):
    """
    Redirects to the url from manipulation_obj.value_1 with a 'vs=' source code
    appended
    """
    url = manipulation_obj.value_1
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
    url = quote_string(redirect_obj.url)
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


def fixurl(redirect_obj, manipulation_obj):
    """
    Replaces value 1 with value 2
    """
    url = redirect_obj.url.replace(manipulation_obj.value_1,
                                   manipulation_obj.value_2)
    return url


def amptoamp(redirect_obj, manipulation_obj):
    """
    Replaces the value before the first ampersand with value_1 and the value
    after the second ampersand with value_2
    """
    url = redirect_obj.url.split('&')
    return manipulation_obj.value_1 + url[1] + manipulation_obj.value_2


def switchlastinstance(redirect_obj, manipulation_obj, old=None, new=None):
    """
    Replaces the last instance of one value with another

    If called on its own, replaces value_1 with value_2; otherwise replaces
    old with new
    """
    old = old or manipulation_obj.value_1
    new = new or manipulation_obj.value_2
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
    url = quote_string(redirect_obj.url)
    url = '%s?url=%s' % (manipulation_obj.value_1, url)
    return 'http://directemployers.us.jobs/companyframe/' + url
