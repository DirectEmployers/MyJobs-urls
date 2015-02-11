from datetime import datetime, timedelta

import factory
from factory import django
from factory import fuzzy

from django.utils import timezone

from redirect import models


class CanonicalMicrositeFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.CanonicalMicrosite

    buid = 0
    canonical_microsite_url = 'http://www.my.jobs/'


class RedirectFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.Redirect

    guid = '{12345678-90ab-cdef-1234-567890abcdef}'
    buid = 0
    uid = None
    url = 'http://www.directemployers.org'
    new_date = datetime.now(tz=timezone.utc) - timedelta(minutes=30)
    # Unused for current testing but may be useful later
    expired_date = None
    job_location = 'Indianapolis'
    job_title = 'Programmer'
    company_name = 'DirectEmployers'


class RedirectArchiveFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.RedirectArchive

    guid = '{12345678-90ab-cdef-1234-567890abcdef}'
    buid = 0
    uid = None
    url = 'http://www.directemployers.org'
    new_date = datetime.now(tz=timezone.utc) - timedelta(60)
    # Unused for current testing but may be useful later
    expired_date = datetime.now(tz=timezone.utc) - timedelta(30)
    job_location = 'Indianapolis'
    job_title = 'Programmer'
    company_name = 'DirectEmployers'


class ViewSourceFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.ViewSource

    view_source_id = 0
    name = 'View Source'
    microsite = True
    include_ga_params = False


class ATSSourceCodeFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.ATSSourceCode

    buid = 0
    view_source_id = 0
    ats_name = 'Indeed Test'
    parameter_name = 'src'
    parameter_value = 'indeed_test'


class RedirectActionFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.RedirectAction

    buid = 0
    view_source_id = 0
    action = models.RedirectAction.SOURCECODETAG_ACTION


class DestinationManipulationFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.DestinationManipulation

    action_type = 1
    action = 'sourcecodetag'
    buid = 0
    view_source = 10
    value_1 = '&codes=DEjn'
    value_2 = '&codes=ArmyRES'


class CustomExcludedViewSourceFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.CustomExcludedViewSource

    buid = 0
    view_source = 1


class ViewSourceGroupFactory(django.DjangoModelFactory):
    FACTORY_FOR = models.ViewSourceGroup

    name = fuzzy.FuzzyText(prefix='Group ')

    @factory.post_generation
    def view_sources(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for view_source in extracted:
                self.view_source.add(view_source)
