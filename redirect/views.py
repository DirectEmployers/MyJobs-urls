from datetime import datetime, timedelta
import uuid

from django.http import *
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import timezone

from redirect.models import Redirect, DestinationManipulation as DM
from redirect import helpers


def home(request, guid, vsid='0', debug=None):
    guid = '{%s}' % uuid.UUID(guid)
    if debug:
        # On localhost ip will always be empty unless you've got a setup
        # that mirrors production
        debug_content = ['ip=%s' % request.META.get('HTTP_X_FORWARDED_FOR', ''),
                         'GUID=%s' % guid]

    guid_redirect = get_object_or_404(Redirect,
                                      guid=guid)
    if debug:
        debug_content.append('RetLink(original)=%s' % guid_redirect.url)

    redirect_url = None
    expired = False
    facebook = False

    clean_guid = guid_redirect.guid.replace("{", "")
    clean_guid = clean_guid.replace("}", "")
    clean_guid = clean_guid.replace("-", "")

    redirect_user_agent = False

    user_agent = request.META.get('HTTP_USER_AGENT')

    # open graph bot redirect
    if 'facebookexternalhit' in str(user_agent):
        user_agent_vs = '1593'
        redirect_user_agent = True

    if 'twitterbot' in str(user_agent):
        user_agent_vs = '1596'
        redirect_user_agent = True

    if 'linkedinbot' in str(user_agent):
        user_agent_vs = '1548'
        redirect_user_agent = True

    if redirect_user_agent:
        company_name = guid_redirect.company_name
        company_name = helpers.quote_string(company_name)
        data = {'title': guid_redirect.job_title,
                 'company': company_name,
                 'guid': clean_guid,
                 'vs': user_agent_vs}
        response = render_to_response('redirect/opengraph.html',
                                      data,
                                      context_instance=RequestContext(request))
    else:
        if vsid == '1604':
            # msccn redirect

            company_name = guid_redirect.company_name
            company_name = helpers.quote_string(company_name)
            redirect_url = ('http://us.jobs/msccn-referral.asp?gi='
                            '%s%s&cp=%s&u=%s' %
                            (clean_guid,
                             vsid,
                             company_name,
                             guid_redirect.uid))
        elif vsid == '294':
            # facebook redirect
            facebook = True

            if guid_redirect.expired_date:
                expired = True

            redirect_url = 'http://apps.facebook.com/us-jobs/?jvid=%s%s' % \
                (clean_guid, vsid)
        else:
            if guid_redirect.expired_date:
                expired = True

            manipulations = None
            # Check for a 'vs' request parameter. If it exists, this is an
            # apply click and vs should be used in place of vsid
            apply_vs = request.REQUEST.get('vs')
            if apply_vs:
                try:
                    apply_vs = int(apply_vs)
                    manipulations = DM.objects.filter(
                        buid=guid_redirect.buid,
                        view_source=apply_vs,
                        action_type=2)
                except ValueError:
                    # Should never happen unless someone manually types in the
                    # url and makes a typo or their browser does something it
                    # shouldn't with links, which is apparently quite common
                    pass
            else:
                manipulations = DM.objects.filter(
                    buid=guid_redirect.buid,
                    view_source=vsid).order_by('action_type')
                if not manipulations and vsid != '0':
                    manipulations = DM.objects.filter(
                        buid=guid_redirect.buid,
                        view_source=0).order_by('action_type')

            if manipulations and not redirect_url:
                new_job = (guid_redirect.new_date + timedelta(minutes=30)) > \
                    datetime.now(tz=timezone.utc)
                previous_manipulation = ''
                for manipulation in manipulations:
                    if (new_job and manipulation.action == 'microsite' and
                            manipulation.action_type == 1):
                        continue
                    elif previous_manipulation == 'microsite':
                        break;
                    previous_manipulation = manipulation.action
                    method_name = manipulation.action
                    if debug:
                        debug_content.append(
                            'ActionTypeID=%s Action=%s' % \
                            (manipulation.action_type,
                             manipulation.action))

                    try:
                        redirect_method = getattr(helpers, method_name)
                    except AttributeError:
                        pass

                    redirect_url = redirect_method(guid_redirect, manipulation)
                    if debug:
                        debug_content.append(
                            'ActionTypeID=%s ManipulatedLink=%s VSID=%s' %
                            (manipulation.action_type,
                             redirect_url,
                             manipulation.view_source))
                    guid_redirect.url = redirect_url

        if not redirect_url:
            redirect_url = guid_redirect.url
            if debug:
                debug_content.append(
                    'ManipulatedLink(No Manipulation)=%s' % redirect_url)

        redirect_url = helpers.get_hosted_state_url(guid_redirect,
                                                    redirect_url)

        if debug:
            debug_content.append('RetLink=%s' % redirect_url)

        if expired:
            err = '&jcnlx.err=XIN'
            data = {'location': guid_redirect.job_location,
                    'title': guid_redirect.job_title}
            if facebook:
                expired_context = 'facebook'
            elif (guid_redirect.buid in [1228, 5480] or
                  2650 <= guid_redirect.buid <= 2703):
                expired_context= 'special'
                if guid_redirect.buid in [1228, 5480]:
                    err = '&jcnlx.err=XJC'
                else:
                    err = '&jcnlx.err=XST'
            else:
                expired_context = 'default'
                redirect_url = guid_redirect.url
                data['buid'] = guid_redirect.buid
                data['company_name'] = guid_redirect.company_name

            data['expired_context'] = expired_context
            data['url'] = redirect_url
            response = HttpResponseGone(
                render_to_string('redirect/expired.html', data))
        else:
            response = HttpResponsePermanentRedirect(redirect_url)

        aguid = request.COOKIES.get('aguid') or \
            helpers.quote_string('{%s}' % str(uuid.uuid4()))
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

    if debug and not redirect_user_agent:
        data = {'debug_content': debug_content}
        return render_to_response('redirect/debug.html',
                                  data,
                                  context_instance=RequestContext(request))
    else:
        return response


def myjobs_redirect(request):
    return HttpResponsePermanentRedirect(
        'http://www.my.jobs' + request.get_full_path())
