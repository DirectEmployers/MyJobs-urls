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
    buid = 0
    uid = 0
    url = 'jobs.jobs'
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
    ats_name = 'Test'
    parameter_name = 'sourcecodetag'
    parameter_value = '&src=JB-11380'   
    

class RedirectActionFactory(factory.Factory):
    FACTORY_FOR = models.RedirectAction
    
    buid = 0
    view_source_id = 0    
    action = 'sourcecodetag'
    
