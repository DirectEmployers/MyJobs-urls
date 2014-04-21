from urllib import quote
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def create_search_urls(job, url):
    location = quote(job.job_location)
    title = quote(job.job_title)
    html = []
    anchor = '<a href="%s" target="_blank" class="drill-search">%s</a>'
    html.append(anchor % ('%sjobs/?q=%s&location=%s' % (url, title,
                                                        location),
                          '%s %s Jobs' % (job.company_name,
                                          job.job_title)))
    html.append(anchor % ('%sjobs/?location=%s' % (url, location),
                          '%s Jobs in %s' % (job.company_name,
                                             job.job_location)))
    html.append(anchor % ('%sjobs/?location=%s' % (url, location[:2]),
                          '%s Jobs in %s' % (job.company_name,
                                             job.job_location[:2])))

    return mark_safe('<br />'.join(html))
