from datetime import datetime

import factory
import pytz

from redirect import models


class CanonicalMicrositeFactory(factory.Factory):
    FACTORY_FOR = models.CanonicalMicrosite

    buid = 0
    canonical_microsite_url = 'jobs.jobs/%s/job'


class RedirectFactory(factory.Factory):
    FACTORY_FOR = models.Redirect

    guid = '1234567890abcdef1234567890abcdef'
    buid = 0
    uid = 0
    url = 'directemployers.org'
    new_date = datetime.now(tz=pytz.utc)
    # Unused for current testing but may be useful later
    expired_date = None
    job_location = ''
    job_title = ''
    company_name = ''


class ViewSourceFactory(factory.Factory):
    FACTORY_FOR = models.ViewSource

    view_source_id = 0
    name = 'View Source'
    microsite = True
    

class ATSSourceCodeFactory(factory.Factory):
    FACTORY_FOR = models.ATSSourceCode
    
    buid = 0
    view_source_id = 0
    ats_name = 'Indeed Test'
    parameter_name = 'src'
    parameter_value = 'indeed_test'   
    

class RedirectActionFactory(factory.Factory):
    FACTORY_FOR = models.RedirectAction
    
    buid = 0
    view_source_id = 0    
    action = models.RedirectAction.SOURCECODETAG_ACTION
