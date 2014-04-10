from datetime import datetime, timedelta
from email.utils import getaddresses
import requests
import urllib
import urllib2
import urlparse

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.http import urlquote_plus
from jira.client import JIRA
from jira.exceptions import JIRAError

import redirect.actions
from redirect.models import CanonicalMicrosite, DestinationManipulation


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


NEW_MJ_CUSTOM_MSG = """
Thank you for your message. We will forward it to the appropriate party in
short order. However, before we do so we need you to verify your email by
activating your my.jobs account. This allows us to verify that you are human
and gives you access to the tools on my.jobs.

To activate your account for %s, just click the link below to verify you own
this email address.
"""


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


def do_manipulations(guid_redirect, manipulations,
                     return_dict, debug_content=None):
    """
    Performs the manipulations denoted by :manipulations:

    Inputs:
    :guid_redirect: Redirect object for this job
    :manipulations: List of DestinationManipulation objects
    :return_dict: Dictionary of values used in all levels of the
        main redirect view
    :debug_content: List of strings that will be output on the debug page

    Modifies:
    :return_dict: Potentially modifies the redirect_url key
    :debug_content: Potentially adds new debug strings
    """
    if manipulations and not return_dict['redirect_url']:
        for manipulation in manipulations:
            method_name = manipulation.action
            if debug_content:
                debug_content.append(
                    'ActionTypeID=%s Action=%s' %
                    (manipulation.action_type,
                     manipulation.action))

            try:
                redirect_method = getattr(redirect.actions, method_name)
            except AttributeError:
                pass
            else:

                if manipulation.action in [
                        'doubleclickwrap', 'replacethenaddpre',
                        'sourceurlwrap', 'sourceurlwrapappend',
                        'sourceurlwrapunencoded',
                        'sourceurlwrapunencodedappend']:
                    # These actions all result in our final url being
                    # appended, usually as a query string, to a value
                    # determined by the manipulation object; due to
                    # this, we should add any custom query parameters
                    # before doing the manipulation.
                    if return_dict['enable_custom_queries']:
                        guid_redirect.url = replace_or_add_query(
                            guid_redirect.url,
                            '&%s' % return_dict.get('qs'),
                            exclusions=['vs', 'z'])
                    redirect_url = redirect_method(guid_redirect,
                                                   manipulation)
                else:
                    redirect_url = redirect_method(guid_redirect,
                                                   manipulation)

                    # manipulations is a QuerySet, which doesn't
                    # support negative indexing; reverse the set and
                    # take the first element to get the last
                    # DestinationManipulation object.
                    if manipulation == manipulations.reverse()[:1][0]:
                        # Only add custom query parameters after
                        # processing the final DestinationManipulation
                        # object to ensure we're not needlessly
                        # replacing them on each iteration.
                        if return_dict['enable_custom_queries']:
                            redirect_url = replace_or_add_query(
                                redirect_url,
                                '&%s' % return_dict.get('qs'),
                                exclusions=['vs', 'z'])
                return_dict['redirect_url'] = redirect_url

                if debug_content:
                    debug_content.append(
                        'ActionTypeID=%s ManipulatedLink=%s VSID=%s' %
                        (manipulation.action_type,
                         return_dict['redirect_url'],
                         manipulation.view_source))

                guid_redirect.url = return_dict['redirect_url']


def get_manipulations(guid_redirect, vs_to_use):
    """
    Retrieves the set of DestinationManipulation objects, if any, for this
    GUID and view source

    Inputs:
    :guid_redirect: Redirect object for this job
    :vs_to_use: View source to retrieve manipulations for

    Outputs:
    :manipulations: List of DestinationManipulation objects, or None if none
        exist
    """
    manipulations = DestinationManipulation.objects.filter(
        buid=guid_redirect.buid,
        view_source=vs_to_use).order_by('action_type')
    if not manipulations and vs_to_use != 0:
        manipulations = DestinationManipulation.objects.filter(
            buid=guid_redirect.buid,
            view_source=0).order_by('action_type')
    return manipulations


def get_redirect_url(request, guid_redirect, vsid, guid, debug_content=None):
    """
    Does the majority of the work in determining what url we should redirect to

    Inputs:
    :request: The current request
    :guid_redirect: Redirect object for the current job
    :vsid: View source for the current request
    :guid: GUID cleared of all undesired characters
    debug_content: List of strings that will be output on the debug page

    Modifies:
    :debug_content: Potentially adds new debug strings
    """
    return_dict = {'redirect_url': None,
                   'expired': False,
                   'facebook': False}
    if guid_redirect.expired_date:
        return_dict['expired'] = True

    if vsid == '294':
        # facebook redirect
        return_dict['facebook'] = True

        return_dict['redirect_url'] = 'http://apps.facebook.com/us-jobs/?jvid=%s%s' % \
                                      (guid, vsid)
    else:
        manipulations = None
        # Check for a 'vs' request parameter. If it exists, this is an
        # apply click and vs should be used in place of vsid
        apply_vs = request.REQUEST.get('vs')
        skip_microsite = False
        vs_to_use = vsid
        if apply_vs:
            skip_microsite = True
            vs_to_use = apply_vs

        # Is this a new job (< 30 minutes old)? Used in conjunction
        # with the set of excluded view sources to determine if we
        # should redirect to a microsite
        new_job = (guid_redirect.new_date + timedelta(minutes=30)) > \
            datetime.now(tz=timezone.utc)

        try:
            microsite = CanonicalMicrosite.objects.get(
                buid=guid_redirect.buid)
        except CanonicalMicrosite.DoesNotExist:
            microsite = None

        if microsite and return_dict.get('expired'):
            return_dict['browse_url'] = microsite.canonical_microsite_url

        try:
            vs_to_use = int(vs_to_use)
        except ValueError:
            # Should never happen unless someone manually types in the
            # url and makes a typo or their browser does something it
            # shouldn't with links, which is apparently quite common
            pass
        else:
            # vs_to_use in settings.EXCLUDED_VIEW_SOURCES or
            # (buid, vs_to_use) in settings.CUSTOM_EXCLUSIONS
            #     The given view source should not redirect to a
            #     microsite
            # microsite is None
            #     This business unit has no associated microsite
            # skip_microsite:
            #     Prevents microsite loops when the vs= parameter
            #     is provided
            # new_job
            #     This job is new and may not have propagated to
            #     microsites yet; skip microsite redirects
            try_manipulations = (
                (vs_to_use in settings.EXCLUDED_VIEW_SOURCES or
                 (guid_redirect.buid, vs_to_use) in settings.CUSTOM_EXCLUSIONS or
                 microsite is None) or skip_microsite or new_job)
            if try_manipulations:
                manipulations = get_manipulations(guid_redirect,
                                                  vs_to_use)
            elif microsite:
                redirect_url = '%s%s/job/?vs=%s' % \
                               (microsite.canonical_microsite_url,
                                guid_redirect.uid,
                                vs_to_use)
                if request.REQUEST.get('z') == '1':
                    # Enable adding vs and z to the query string; these
                    # will be passed to the microsite, which will pass
                    # them back to us on apply clicks
                    redirect_url = replace_or_add_query(
                        redirect_url, '&%s' % request.META.get('QUERY_STRING'),
                        exclusions=[])
                return_dict['redirect_url'] = redirect_url

            return_dict['enable_custom_queries'] = request.REQUEST.get('z') == '1'
            return_dict['qs'] = request.META['QUERY_STRING']
            do_manipulations(guid_redirect, manipulations,
                             return_dict, debug_content)

    return return_dict


def get_opengraph_redirect(request, redirect, guid):
    response = None
    user_agent_vs = None
    user_agent = request.META.get('HTTP_USER_AGENT', ''),

    # open graph bot redirect
    if 'facebookexternalhit' in user_agent:
        user_agent_vs = '1593'

    elif 'twitterbot' in user_agent:
        user_agent_vs = '1596'

    elif 'linkedinbot' in user_agent:
        user_agent_vs = '1548'

    if user_agent_vs:
        company_name = redirect.company_name
        company_name = quote_string(company_name)
        data = {'title': redirect.job_title,
                'company': company_name,
                'guid': guid,
                'vs': user_agent_vs}
        response = render_to_response('redirect/opengraph.html',
                                      data,
                                      context_instance=RequestContext(request))
    return user_agent_vs, response


def replace_or_add_query(url, query, exclusions=None):
    """
    Adds field/value pair to the provided url as a query string if the
    key isn't already in the url, or replaces it otherwise.

    Appends the proper pair separator (?&) based on the input url

    Inputs:
    :url: URL that query string should be appended to
    :query: Query string(s) to add to :url:
    :exclusions: List of keys that should not be copied; common keys
        include 'vs' and 'z'

    Outputs:
    :url: Input url with query string appended
    """
    if not exclusions:
        exclusions = []
    if len(query) > 1 and query[0] in ['?', '&']:
        query = query[1:]
        query = query.encode('utf-8')
        url = url.encode('utf-8')
        url = urlparse.urlparse(url)
        old_query = urlparse.parse_qsl(url.query, keep_blank_values=True)
        old_keys = [q[0] for q in old_query]

        new_query = urlparse.parse_qsl(query)

        for new_index in range(len(new_query)):
            if new_query[new_index][0] not in exclusions:
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
        url = urlparse.urlunparse(url)
    else:
        parts = url.split('#')
        parts[0] += query
        url = '#'.join(parts)
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


def add_part(body, part, value, join_str):
    """
    Constructs parts of a JIRA ticket (or email) body,  bit by bit.

    Inputs:
    :body: Current body that we will append to
    :part: Name of the current thing we are appending
    :value: What we are going to append
    :join_str: String that will be used to join the value together if
        it is a list

    Outputs:
    :body: Input body with a name and value appended to it
    """
    if type(value) == list:
        value = join_str.join(value)
    if join_str == '\n':
        body_part = '%s:\n%s\n'
    else:
        body_part = '%s: %s\n'
    body += body_part % (part, value)
    return body


def log_failure(post, subject=None):
    """
    Logs failures in redirecting job@my.jobs emails. This does not mean literal
    failure, but the email in question is not a guid@my.jobs email and should be forwarded.

    Inputs:
    :post: copy of request.POST QueryDict
    """

    if settings.DEBUG or hasattr(mail, 'outbox'):
        jira = []
    else:
        try:
            jira = JIRA(options=settings.JIRA_OPTIONS,
                        basic_auth=settings.JIRA_AUTH)
        except JIRAError:
            jira = []

    # Pop from and headers from the post dict; from is used in a few places
    # and headers, text, and html need a small bit of special handling
    from_ = post.pop('from', '')
    if type(from_) == list:
        from_ = from_[0]
    headers = post.pop('headers', '')
    text = post.pop('text', '')
    html = post.pop('html', '')
    body = add_part('', 'from', from_, '')

    # These are likely to be the most important, so we can put them first
    for part in ['to', 'cc', 'subject', 'spam_score', 'spam_report']:
        body = add_part(body, part, post.pop(part, ''), ', ')

    # Add email body (text and html versions)
    body = add_part(body, 'text', text, '\n')
    body = add_part(body, 'html', html, '\n')

    for item in post.items():
        if not item[0].startswith('attachment'):
            body = add_part(body, item[0], item[1], ', ')

    body = add_part(body, 'headers', headers, '\n')

    if subject is None:
        subject = 'My.jobs contact email'
    if jira:
        project = jira.project('MJA')
        issue = {
            'project': {'key': project.key},
            'summary': subject,
            'description': body,
            'issuetype': {'name': 'Task'}
        }
        jira.create_issue(fields=issue)
    else:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_,
            to=[settings.EMAIL_TO_ADMIN])
        email.send()


def send_response_to_sender(from_, to, response_type):
    email = EmailMessage(from_email=from_,
                         to=to,
                         subject='Error sending email')
    if response_type == 'no_match':
        email.body = 'TODO: Create template for this (does not match job)'
    else:
        email.body = 'TODO: Create template for this (matches job)'
    email.send()


def create_myjobs_account(from_email):
    """
    Creates a My.jobs account for a given email if one does not exist

    Inputs:
    :from_email: Email address that will be associated with the new
        My.jobs account

    Returns:
    Response from My.jobs (or an error) if tests are not being run
    My.jobs url if tests are being run
    """
    if type(from_email) != list:
        from_email = [from_email]
    # getaddresses returns a list of tuples
    # ['name@example.com'] parses to [('', 'name@example.com')]
    # ['Name <name@example.com>'] parses to [('Name', 'name@example.com')]
    from_email = getaddresses(from_email)[0][1]
    mj_url = 'http://secure.my.jobs:80/api/v1/user/'
    mj_url = urlparse.urlparse(mj_url)
    qs = {'username': settings.MJ_API['username'],
          'api_key': settings.MJ_API['key'],
          'email': from_email,
          'user_type': 'redirect',
          'custom_msg': NEW_MJ_CUSTOM_MSG % from_email}
    qs = urllib.urlencode(qs)
    mj_url = mj_url._replace(query=qs).geturl()
    if hasattr(mail, 'outbox'):
        return mj_url

    try:
        contents = urllib2.urlopen(mj_url).read()
    except urllib2.URLError as e:
        contents = '{"error":"%s"}' % e.args[0]
    return contents


def repost_to_mj(post, files):
    """
    Repost a parsed email to secure.my.jobs

    Inputs:
    :post: dictionary to be posted
    :files: list containing filename, contents, and content type of files
        to be posted
    """
    post['key'] = settings.EMAIL_KEY
    mj_url = 'https://secure.my.jobs/prm/email'
    if not hasattr(mail, 'outbox'):
        new_files = {}
        for index in range(len(files)):
            # This fails when we include content type for some reason;
            # Don't send content type
            new_files['attachment%s' % (index+1, )] = files[index][:2]
        r = requests.post(mj_url, data=post, files=new_files)
