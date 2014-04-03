import base64
from email.utils import getaddresses
from datetime import datetime
from itertools import chain
import json
from urllib import unquote
import urllib2
import uuid

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.http import (HttpResponseGone, HttpResponsePermanentRedirect,
                         HttpResponse)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import text, timezone
from django.views.decorators.csrf import csrf_exempt

from myjobs.models import User
from redirect.models import (Redirect, CanonicalMicrosite,
    DestinationManipulation, CompanyEmail, EmailRedirectLog)
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


@csrf_exempt
def email_redirect(request):
    """
    Accepts a post from SendGrid's mail parsing webhook and processes it.

    Address is not a guid:
        Log issue to JIRA (MJA), or email MyJobs admin if that fails
    Address is not in database:
        TODO: Send error to sender
    Address is in database but no company contact exists:
        TODO: Send job description to sender
    Address is in database and a company user exists:
        TODO: Send confirmation to original sender
        Forward email to company contact

    Authentication issues return a status code of 403
    All other paths return a 200 to prevent SendGrid from sending the same
        email repeatedly
    """
    if request.method == 'POST':
        if 'HTTP_AUTHORIZATION' in request.META:
            method, details = request.META['HTTP_AUTHORIZATION'].split()
            if method.lower() == 'basic':
                login_info = base64.b64decode(details).split(':')
                if len(login_info) == 2:
                    login_info[0] = urllib2.unquote(login_info[0])
                    user = authenticate(username=login_info[0],
                                        password=login_info[1])
                    target = User.objects.get(email='accounts@my.jobs')
                    if user is not None and user == target:
                        try:
                            to_email = request.POST.get('to', None)
                            if to_email and type(to_email) != list:
                                to_email = [to_email]
                            elif not to_email:
                                to_email = []
                            body = request.POST.get('text', '')
                            html_body = request.POST.get('html', '')
                            from_email = request.POST.get('from', '')
                            cc = request.POST.get('cc', None)
                            if cc and type(cc) != list:
                                cc = [cc]
                            elif not cc:
                                cc = []
                            subject = request.POST.get('subject', '')
                            num_attachments = int(request.POST['attachments'])
                        except (KeyError, ValueError):
                            # KeyError: key was not in POST dict
                            # ValueError: num_attachments could not be cast
                            #     to int
                            return HttpResponse(status=200)

                        attachment_data = []
                        for file_number in range(1, num_attachments+1):
                            try:
                                file_ = request.FILES['attachment%s' % file_number]
                            except KeyError:
                                # Upload problem?
                                helpers.log_failure(request.POST.copy(),
                                                    'My.jobs Attachment Failure')
                                return HttpResponse(status=200)
                            name = file_.name
                            content = file_.read()
                            content_type = file_.content_type
                            attachment_data.append((name, content, content_type))

                        addresses = getaddresses(to_email + cc)
                        individual = [addr[1].lower() for addr in addresses]

                        if 'prm@my.jobs' in individual:
                            # post to my.jobs
                            helpers.repost_to_mj(request.POST.copy(),
                                                 attachment_data)
                            return HttpResponse(status=200)
                        if len(individual) != 1:
                            # >1 recipients
                            # or 0 recipients (everyone is bcc)
                            # Probably not a guid@my.jobs email
                            helpers.log_failure(request.POST.dict())
                            return HttpResponse(status=200)
                        to_guid = addresses[0][1].split('@')[0]

                        # shouldn't happen, but if someone somehow sends an
                        # email with a view source attached, we should
                        # remove it
                        to_guid = to_guid[:32]
                        try:
                            to_guid = '{%s}' % uuid.UUID(to_guid)
                            job = Redirect.objects.get(guid=to_guid)
                        except ValueError:
                            helpers.log_failure(request.POST.dict())
                            return HttpResponse(status=200)
                        except Redirect.DoesNotExist:
                            # TODO: improve copy for send_response_to_sender
                            # TODO: and send an error email to the sender
                            return HttpResponse(status=200)

                        helpers.create_myjobs_account(from_email)

                        try:
                            ce = CompanyEmail.objects.get(buid=job.buid)
                            new_to = ce.email
                        except CompanyEmail.DoesNotExist:
                            # TODO: send job description to sender
                            return HttpResponse(status=200)

                        # TODO: send job description and forward note to sender

                        sg_headers = {
                            'X-SMTPAPI': '{"category": "My.jobs email redirect"}'
                        }

                        # We reached this point; the data should be good
                        email = EmailMultiAlternatives(
                            to=[new_to], from_email=from_email, subject=subject,
                            body=body, cc=cc, headers=sg_headers)
                        email.attach_alternative(html_body, 'text/html')
                        for attachment in attachment_data:
                            email.attach(*attachment)
                        email.send()

                        log = {'from_addr': from_email,
                               'to_guid': to_guid,
                               'buid': job.buid,
                               'to_addr': new_to}
                        EmailRedirectLog.objects.create(**log)

                        return HttpResponse(status=200)
    return HttpResponse(status=403)


def update_buid(request):
    """
    API for updating business units
    """
    old = request.GET.get('old_buid', None)
    new = request.GET.get('new_buid', None)
    key = request.GET.get('key', None)

    data = {'error': ''}

    if settings.BUID_API_KEY != key:
        data['error'] = 'Unauthorized'
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=401)

    try:
        old = int(request.GET.get('old_buid', None))
    except (ValueError, TypeError):
        data = {'error': 'Invalid format for old business unit'}
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=400)

    try:
        new = int(request.GET.get('new_buid', None))
    except (ValueError, TypeError):
        data = {'error': 'Invalid format for new business unit'}
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=400)

    if CanonicalMicrosite.objects.filter(buid=new) or \
         DestinationManipulation.objects.filter(buid=new):
        data = {'error': 'New business unit already exists'}
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=400)

    try:
        cm = CanonicalMicrosite.objects.get(buid=old)
    except CanonicalMicrosite.DoesNotExist:
        num_instances = 0
    else:
        num_instances = 1
        cm.buid = new
        cm.save()

    dms = DestinationManipulation.objects.filter(buid=old)
    for dm in dms:
        dm.pk = None
        dm.id = None
        dm.buid = new
        dm.save()
    num_instances += dms.count()

    data.pop('error')
    data['updated'] = num_instances
    data['new_bu'] = new
    return HttpResponse(json.dumps(data),
                        content_type='application/json')
