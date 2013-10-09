from datetime import datetime, timedelta
import uuid

from django.http import *
from django.shortcuts import get_object_or_404, render_to_response
from django.utils import timezone

from redirect import models
from redirect import helpers


def home(request, guid, vsid='0'):
    guid_redirect = get_object_or_404(models.Redirect,
                                      guid='{%s}' % uuid.UUID(guid))

    try:
        manipulation = models.DestinationManipulation.objects.get(
            buid=guid_redirect.buid, view_source=vsid, action_type=1)
    except models.DestinationManipulation.DoesNotExist:
        try:
            manipulation = models.DestinationManipulation.objects.get(
                buid=guid_redirect.buid, view_source=vsid)
        except models.DestinationManipulation.DoesNotExist:
            raise Http404

    expired = False
    facebook = False

    clean_guid = guid_redirect.guid.replace("{","")
    clean_guid = clean_guid.replace("}","")
    clean_guid = clean_guid.replace("-","")
    
    redirect_user_agent = False
    
    user_agent = request.META.get('HTTP_USER_AGENT')
    
    # open graph bot redirect
    if 'facebookexternalhit' in str(user_agent):
        user_agent_vs = 1593
        redirect_user_agent = True
    
    if 'twitterbot' in str(user_agent):
        user_agent_vs = 1596
        redirect_user_agent = True
        
    if 'linkedinbot' in str(user_agent):
        user_agent_vs = 1548
        redirect_user_agent = True
    
    if redirect_user_agent:
        company_name = guid_redirect.company_name
        company_name = helpers.quote_string(company_name)
        
        html = "<html>"
        html += ("<head prefix='og: http://ogp.me/ns# fb: http://ogp.me/ns/fb#"
                 " website: http://ogp.me/ns/website#'>")
        html += "<title>US.jobs - %s - %s</title>" % (guid_redirect.job_title, 
                                                      company_name)
        html += ("<meta property='og:description' content='The US.jobs National"
                 " Labor Exchange is a free job search service of "
                 "DirectEmployers Association.' />")
        html += ("<meta property='og:image' content='http://profile.ak."
                 "fbcdn.net/hprofile-ak-ash2/50226_125241814265748_3627"
                 "96096_n.jpg' />")
        html += "<meta property='og:locale' content='en_US' />"
        html += "<meta property='og:site_name' content='US.jobs' />"
        html += ("<meta property='og:title' content='US.jobs - %s - %s' />" 
                 % (guid_redirect.job_title, company_name))
        html += "<meta property='og:type' content='article' />"
        html += ("<meta property='og:url' content='http://r.my.jobs/%s%s' />" 
                 % (clean_guid, user_agent_vs))
        html += "</head>"
        html += "</html>"        
        response = HttpResponse(content=html, mimetype='text/html')
    else:    
        if manipulation.view_source == 1604:
            # msccn redirect
    
            company_name = guid_redirect.company_name
            company_name = helpers.quote_string(company_name)
            redirect_url = ('http://us.jobs/msccn-referral.asp?gi='
                            '%s%s&cp=%s&u=%s' %
                            (clean_guid,
                             manipulation.view_source,
                             company_name,
                             guid_redirect.uid))
        elif manipulation.view_source == 294:
            # facebook redirect
            facebook = True
    
            if guid_redirect.expired_date:
                expired = True
    
            redirect_url = 'http://apps.facebook.com/us-jobs/?jvid=%s%s' % \
                (clean_guid, manipulation.view_source)
        else:
            if guid_redirect.expired_date:
                expired = True
    
            method_name = manipulation.action
    
            try:
                redirect_method = getattr(helpers, method_name)
            except AttributeError:
                pass
    
            redirect_url = redirect_method(guid_redirect, manipulation)
    
        aguid = request.COOKIES.get('aguid') or \
            helpers.quote_string('{%s}' % str(uuid.uuid4()))
        if expired:
            err = '&jcnlx.err=XIN'
            if facebook:
                expired = ('Please <a href="http://us.jobs/" target="_blank">'
                           'visit US.jobs</a> and continue with your job '
                           'search.')
            elif (guid_redirect.buid in [1228, 5480]
                  or 2650 <= guid_redirect.buid <= 2703):
                expired = ('Please <a href="#" onclick="window.close();return '
                           'false;">close this window</a> and continue with '
                           'your job search.')
                if guid_redirect.buid in [1228, 5480]:
                    err = '&jcnlx.err=XJC'
                else:
                    err = '&jcnlx.err=XST'
            else:
                expired = ('Please <a href="#" onclick="window.close();return '
                           'false;">close this window</a> and continue with '
                           'your job search, or visit the National Labor '
                           'Exchange to view all current jobs for <a href="'
                           'http://us.jobs/results.asp?bu=%s">%s</a>.' %
                           (guid_redirect.buid, guid_redirect.company_name))
            response = render_to_response('redirect/expired.html',
                                          {'url': redirect_url,
                                           'location': guid_redirect.job_location,
                                           'title': guid_redirect.job_title,
                                           'expired': expired})
        else:
            response = HttpResponsePermanentRedirect(redirect_url)
    
        qs = 'jcnlx.ref=%s&jcnlx.url=%s&jcnlx.buid=%s&jcnlx.vsid=%s&jcnlx.aguid=%s'
        qs %= (helpers.quote_string(request.META.get('HTTP_REFERER')),
               helpers.quote_string(redirect_url),
               guid_redirect.buid,
               vsid,
               aguid)
        if expired:
            now = datetime.now(tz=timezone.utc)
            d_hours = int((now - guid_redirect.expired_date).total_seconds() / 60 / 60)
            qs += '%s&jcnlx.xhr=%s' % (err, d_hours)
        response['X-REDIRECT'] = qs
        response.set_cookie('aguid', aguid,
                            expires=365*24*60*60,
                            domain='.my.jobs')
    return response
