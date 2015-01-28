import datetime

from redirect.models import Redirect, RedirectArchive


def expired_to_archive_table():
    """
    Moves all redirects that have been expired for more than
    thirty days from Redirect to RedirectArchive.

    """
    thirty_days_ago = datetime.date.today() - datetime.timedelta(30)
    expired = Redirect.objects.filter(expired_date__lte=thirty_days_ago)
    add_redirects(RedirectArchive, expired)
    expired.delete()


def unexpired_to_active_table():
    """
    Moves anything that isn't actually expired (expired_date==None) from
    RedirectArchive to Redirect

    """
    not_expired = RedirectArchive.objects.filter(expired_date__isnull=True)
    add_redirects(Redirect, not_expired)
    not_expired.delete()


def add_redirects(to_model, redirects):
    """
    Adds an iteratble of redirects to to_model.

    :param to_model: A subclass of BaseRedirect (either
                     Redirect or RedirectArchive) that will
                     be getting the copies of the redirects.
    :param redirects: An iterable of redirect objects that should
                      be added to the to_model table.
    """
    new_redirects = []
    for redirect in redirects:
        new_redirects.append(copy_redirect(to_model, redirect))
    to_model.objects.bulk_create(new_redirects)


def copy_redirect(model, existing_redirect):
    """
    Makes a new copy of a redirect.

    :param model: A subclass of BaseRedirect (either
                  Redirect or RedirectArchive) that the new
                  redirect should be made for.
    :param existing_redirect: An existing redirect instance that the new
                              redirect should copy from.

    :return: An instace of model with data copied from existing_redirect.
             This instance has not yet been written to the table
             for model.

    """
    return model(guid=existing_redirect.guid,
                 buid=existing_redirect.buid,
                 uid=existing_redirect.uid,
                 url=existing_redirect.url,
                 new_date=existing_redirect.new_date,
                 expired_date=existing_redirect.expired_date,
                 job_location=existing_redirect.job_location,
                 job_title=existing_redirect.job_title,
                 company_name=existing_redirect.company_name)