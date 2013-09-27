from datetime import datetime

import factory
import pytz

from redirect import models


class CanonicalMicrositeFactory(factory.Factory):
    FACTORY_FOR = models.CanonicalMicrosite

    buid = 0
    canonical_microsite_url = 'jobs.jobs/[Unique_ID]/job'


class RedirectFactory(factory.Factory):
    FACTORY_FOR = models.Redirect

    guid = '12345678-90ab-cdef-1234-567890abcdef'
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


class DestinationManipulationFactory(factory.Factory):
    FACTORY_FOR = models.DestinationManipulation

    action_type = 1
    action = 'sourcecodetag'
    buid = 0
    view_source = 0
    value_1 = '&codes=DEjn'
    value_2 = '&codes=ArmyRES'
