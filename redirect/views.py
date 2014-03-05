import base64
from datetime import datetime
import urllib2
import uuid

import sendgrid

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import (HttpResponseGone, HttpResponsePermanentRedirect,
                         HttpResponse)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import text, timezone
from django.views.decorators.csrf import csrf_exempt

from redirect.models import Redirect, CompanyEmail, EmailRedirectLog
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
                    target = User.objects.get(username='accounts@my.jobs')
                    if user is not None and user == target:
                        try:
                            to_email = request.POST['to']
                            # Unused currently but is always sent
                            #headers = request.POST['headers']
                            body = request.POST['text']
                            html_body = request.POST['html']
                            from_email = request.POST['from']
                            cc = request.POST['cc']
                            subject = request.POST['subject']
                            num_attachments = int(request.POST['attachments'])
                        except (KeyError, ValueError):
                            # KeyError: key was not in POST dict
                            # ValueError: num_attachments could not be cast
                            #     to int
                            return HttpResponse(status=200)

                        to_guid = to_email.split('@')[0]

                        # shouldn't happen, but if someone somehow sends an
                        # email with a view source attached, we should
                        # remove it
                        to_guid = to_guid[:32]
                        try:
                            to_guid = '{%s}' % uuid.UUID(to_guid)
                            job = Redirect.objects.get(guid=to_guid)
                        except ValueError, e:
                            helpers.log_failure(from_=from_email, to=to_email,
                                                message=e.message)
                            return HttpResponse(status=200)
                        except Redirect.DoesNotExist:
                            return HttpResponse(status=200)

                        try:
                            ce = CompanyEmail.objects.get(buid=job.buid)
                            new_to = ce.email
                        except CompanyEmail.DoesNotExist:
                            return HttpResponse(status=200)

                        file_names = []
                        try:
                            for file_num in range(1, num_attachments+1):
                                file_names.append(getattr(request.POST,
                                                          'attachment%s' % (
                                                              file_num,)))
                        except AttributeError:
                            # getattr could not find an expected attachment
                            return HttpResponse(status=200)

                        attachment_data = []
                        for file_name in file_names:
                            try:
                                file_ = request.FILES[file_name]
                            except KeyError:
                                # Upload problem?
                                return HttpResponse(status=200)
                            name = file_.name
                            content = file_.read()
                            attachment_data.append((name, content))

                        # We reached this point; the data should be good
                        email = sendgrid.Mail(to=new_to, subject=subject,
                                              html=html_body, text=body,
                                              from_email=from_email, bcc=cc)
                        for addr in cc:
                            # the sendgrid library supports bcc but not cc;
                            # add anyone who was cc'd to the 'to' portion
                            email.add_to(addr)
                        for attachment in attachment_data:
                            email.add_attachment_stream(*attachment)
                        email.add_category('My.jobs email redirect')

                        sg = sendgrid.SendGridClient(
                            settings.EMAIL_HOST_USER,
                            settings.EMAIL_HOST_PASSWORD)
                        status, msg = sg.send(email)

                        log = {'from_addr': from_email,
                               'to_guid': to_guid,
                               'buid': job.buid,
                               'to_addr': new_to}
                        EmailRedirectLog.objects.create(**log)

                        if status != 200:
                            helpers.log_failure(from_=from_email, to=new_to,
                                                message=msg)
                        return HttpResponse(status=200)
    return HttpResponse(status=403)
