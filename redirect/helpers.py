import urllib
import urlparse

from django.utils.http import urlquote_plus


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


def clean_guid(guid):
    """
    Removes non-hex characters from the provided GUID.

    Inputs:
    :guid: GUID to be cleaned

    Outputs:
    :cleaned_guid: GUID with any offending characters removed
    """
    cleaned_guid = guid.replace("{", "")
    cleaned_guid = cleaned_guid.replace("}", "")
    return cleaned_guid.replace("-", "")


def replace_or_add_query(url, query):
    """
    Adds field/value pair to the provided url as a query string if the
    key isn't already in the url, or replaces it otherwise.

    Appends the proper pair separator (?&) based on the input url

    Inputs:
    :url: URL that query string should be appended to
    :query: Query string(s) to add to :url:

    Outputs:
    :url: Input url with query string appended
    """
    query = query.encode('utf-8')
    url = url.encode('utf-8')
    url = urlparse.urlparse(url)
    old_query = urlparse.parse_qsl(url.query, keep_blank_values=True)
    old_keys = [q[0] for q in old_query]

    new_query = urlparse.parse_qsl(query)

    for new_index in range(len(new_query)):
        if new_query[new_index][0] in old_keys:
            old_index = old_keys.index(new_query[new_index][0])
            old_query[old_index] = new_query[new_index]
        else:
            old_query.append(new_query[new_index])

    # parse_qsl unencodes the query that you pass it; Re-encode the query
    # parameters when reconstructing the string.
    old_query = '&'.join(['='.join([urllib.quote(k), urllib.quote(v)])
                         for k, v in old_query])
    url = url._replace(query=old_query)
    return urlparse.urlunparse(url)


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


def set_aguid_cookie(response, host, aguid):
    """
    Sets an aguid cookie using the same domain as was requested. Does not work
    if hosted on a two-level TLD (.com.<country_code>, for example)

    Inputs:
    :response: HttpResponse (or a subclass) object prior to setting the cookie
    :host: HTTP_HOST header
    :aguid: aguid for the current user, either retrieved from a cookie for a
        repeat visitor or calculated anew for a new user

    Outputs:
    :response: Input :response: with an added aguid cookie
    """
    # The test client does not send a HTTP_HOST header by default; don't try
    # to set a cookie if there is no host
    if host:
        # Remove port, if any
        host = host.split(':')[0]

        # Assume that whatever is after the last period is the tld
        # Whatever is before the tld should be the root domain
        host = host.split('.')[-2:]

        # Reconstruct the domain for use in a cookie
        domain = '.' + '.'.join(host[-2:])

        # Sets a site-wide cookie
        # Works for "normal" domains (my.jobs, jcnlx.com), but doesn't set a
        # cookie if accessed via localhost (depends on browser, apparently)
        # or IP
        response.set_cookie('aguid', aguid,
                            expires=365 * 24 * 60 * 60,
                            domain=domain)
    return response
