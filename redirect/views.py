from datetime import datetime
from urllib import unquote
import uuid

from django.http import HttpResponseGone, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import text, timezone

from redirect.models import Redirect
from redirect import helpers


def home(request, guid, vsid=None, debug=None):
    if vsid is None:
        vsid = '0'
    guid = '{%s}' % uuid.UUID(guid)

    # Providing z=1 as a query parameter enables custom parameters
    enable_custom_queries = request.REQUEST.get('z') == '1'
    expired = False

    if debug:
        # On localhost ip will always be empty unless you've got a setup
        # that mirrors production
        debug_content = ['ip=%s' % request.META.get('HTTP_X_FORWARDED_FOR', ''),
                         'GUID=%s' % guid]
        if enable_custom_queries:
            debug_content.append('CustomParameters=%s' %
                                 request.META.get('QUERY_STRING'))

    guid_redirect = get_object_or_404(Redirect,
                                      guid=guid)
    if debug:
        debug_content.append('RetLink(original)=%s' % guid_redirect.url)

    cleaned_guid = helpers.clean_guid(guid_redirect.guid)

    user_agent_vs, response = helpers.get_opengraph_redirect(request,
                                                             guid_redirect,
                                                             cleaned_guid)

    if not user_agent_vs:
        if vsid == '1604':
            # msccn redirect

            company_name = guid_redirect.company_name
            company_name = helpers.quote_string(company_name)
            redirect_url = ('http://us.jobs/msccn-referral.asp?gi='
                            '%s%s&cp=%s&u=%s' %
                            (cleaned_guid,
                             vsid,
                             company_name,
                             guid_redirect.uid))
        else:
            args = {'request': request, 'guid_redirect': guid_redirect,
                    'vsid': vsid, 'guid': cleaned_guid}
            if debug:
                args['debug_content'] = debug_content
            returned_dict = helpers.get_redirect_url(**args)
            redirect_url = returned_dict.get('redirect_url', '')
            facebook = returned_dict.get('facebook', False)
            expired = returned_dict.get('expired', False)
            browse_url = returned_dict.get('browse_url', '')
        if not redirect_url:
            redirect_url = guid_redirect.url
            if debug:
                debug_content.append(
                    'ManipulatedLink(No Manipulation)=%s' % redirect_url)
            if enable_custom_queries:
                redirect_url = helpers.replace_or_add_query(
                    redirect_url, request.META.get('QUERY_STRING'),
                    exclusions=['vs', 'z'])
                if debug:
                    debug_content.append(
                        'ManipulatedLink(Custom Parameters)=%s' % redirect_url)
        redirect_url = helpers.get_hosted_state_url(guid_redirect,
                                                    redirect_url)

        if debug:
            debug_content.append('RetLink=%s' % redirect_url)

        if expired:
            err = '&jcnlx.err=XIN'
            data = {'location': guid_redirect.job_location,
                    'title': guid_redirect.job_title,
                    'company_name': guid_redirect.company_name}
            if (guid_redirect.buid in [1228, 5480] or
                  2650 <= guid_redirect.buid <= 2703):
                if guid_redirect.buid in [1228, 5480]:
                    err = '&jcnlx.err=XJC'
                else:
                    err = '&jcnlx.err=XST'

            data['expired_url'] = redirect_url
            if browse_url:
                data['browse_url'] = browse_url
            else:
                data['browse_url'] = 'http://www.my.jobs/%s/careers/' % \
                    text.slugify(guid_redirect.company_name)
            response = HttpResponseGone(
                render_to_string('redirect/expired.html', data))
        else:
            response = HttpResponsePermanentRedirect(redirect_url)

        aguid = request.COOKIES.get('aguid') or \
            uuid.uuid4().hex
        if '%' in aguid:
            aguid = uuid.UUID(unquote(aguid)).hex
        myguid = request.COOKIES.get('myguid', '')
        buid = helpers.get_Post_a_Job_buid(guid_redirect)
        qs = 'jcnlx.ref=%s&jcnlx.url=%s&jcnlx.buid=%s&jcnlx.vsid=%s&jcnlx.aguid=%s&jcnlx.myguid=%s'
        qs %= (helpers.quote_string(request.META.get('HTTP_REFERER', '')),
               helpers.quote_string(redirect_url),
               buid,
               vsid,
               aguid,
               myguid)
        if expired:
            now = datetime.now(tz=timezone.utc)
            d_seconds = (now - guid_redirect.expired_date).total_seconds()
            d_hours = int(d_seconds / 60 / 60)
            qs += '%s&jcnlx.xhr=%s' % (err, d_hours)
        response['X-REDIRECT'] = qs

        response = helpers.set_aguid_cookie(response,
                                            request.get_host(),
                                            aguid)

    if debug and not user_agent_vs:
        data = {'debug_content': debug_content}
        return render_to_response('redirect/debug.html',
                                  data,
                                  context_instance=RequestContext(request))
    else:
        return response


def myjobs_redirect(request):
    return HttpResponsePermanentRedirect(
        'http://www.my.jobs' + request.get_full_path())
