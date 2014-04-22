from urllib import quote
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def create_search_urls(job, url):
    location = quote(job.job_location)
    title = quote(job.job_title)
    html = []
    anchor = '<a href="{href}" target="_blank" class="drill-search">{link_text}</a>'
    html.append(anchor.format(
        href='{base}jobs/?q={query}&location={location}'.format(
            base=url, query=title, location=location),
        link_text='{company} {title} Jobs'.format(
            company=job.company_name, title=job.job_title)))
    html.append(anchor.format(
        href='{base}jobs/?location={location}'.format(
            base=url, location=location),
        link_text='{company} Jobs in {location}'.format(
            company=job.company_name, location=job.job_location)))
    html.append(anchor.format(
        href='{base}jobs/?location={location}'.format(
            base=url, location=location[:2]),
        link_text='{company} Jobs in {location}'.format(
            company=job.company_name, location=job.job_location[:2])))

    return mark_safe('<br />'.join(html))
