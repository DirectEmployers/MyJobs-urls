from urllib import quote
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def create_search_urls(job, url):
    location = job.job_location.encode('utf-8')
    location = quote(location)

    title = job.job_title.encode('utf-8')
    title = quote(title)
    html = []
    anchor = u'<a href="{href}" target="_blank" class="drill-search">{link_text}</a>'
    html.append(anchor.format(
        href=u'{base}jobs/?q={query}&location={location}'.format(
            base=url, query=title, location=location),
        link_text=u'{company} {title} Jobs'.format(
            company=job.company_name, title=job.job_title)))
    html.append(anchor.format(
        href=u'{base}jobs/?location={location}'.format(
            base=url, location=location),
        link_text=u'{company} Jobs in {location}'.format(
            company=job.company_name, location=job.job_location)))
    html.append(anchor.format(
        href=u'{base}jobs/?location={location}'.format(
            base=url, location=location[:2]),
        link_text=u'{company} Jobs in {location}'.format(
            company=job.company_name, location=job.job_location[:2])))

    return mark_safe(u'<br />'.join(html))
