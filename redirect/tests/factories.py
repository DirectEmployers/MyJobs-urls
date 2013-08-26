from datetime import datetime

import factory
import pytz

from redirect import models


class CanonicalMicrositeFactory(factory.Factory):
    FACTORY_FOR = models.CanonicalMicrosite

    buid = 0
    canonical_microsite_url = 'jobs.jobs'

class RedirectFactory(factory.Factory):
    FACTORY_FOR = models.Redirect

    guid = '1234567890abcdef1234567890abcdef'
    buid = factory.SubFactory(CanonicalMicrositeFactory)
    url = 'jobs.jobs'
    new_date = datetime.now(tz=pytz.utc)

class ViewSourceFactory(factory.Factory):
    FACTORY_FOR = models.ViewSource

    viewsource_id = 0
    name = 'View Source'
    microsite = True