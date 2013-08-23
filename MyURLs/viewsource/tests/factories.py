from datetime import datetime
import factory
import pytz

from viewsource.models import ViewSource


class ViewSourceFactory(factory.Factory):
    FACTORY_FOR = ViewSource

    name = 'Named View Source'
    viewsource_id = None
    partner_name = 'DirectEmployers'
    partner_url = 'directemployers.org'
    source_code = '&code=DE'
    redirect_url = 'jobs.jobs/'
    date_new = datetime.now(tz=pytz.utc)
