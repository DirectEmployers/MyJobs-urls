import datetime
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _


class CustomUserManager(BaseUserManager):
    def get_email_owner(self, email):
        """
        Tests if the specified email is already in use.

        Inputs:
        :email: String representation of email to be checked

        Outputs:
        :user: User object if one exists; None otherwise
        """
        try:
            user = self.get(email__iexact=email)
        except User.DoesNotExist:
            try:
                user = self.get(
                    profileunits__secondaryemail__email__iexact=email)
            except User.DoesNotExist:
                user = None
        return user

    def create_inactive_user(self, **kwargs):
        """
        Creates an inactive user, calls the regisration app to generate a
        key and sends an activation email to the user.

        Inputs:
        :send_email: Boolean defaulted to true to signal that an email needs to
        be sent.
        :kwargs: Email and password information

        Outputs:
        :user: User object instance
        :created: Boolean indicating whether a new user was created
        """
        email = kwargs.get('email')
        password = kwargs.get('password1')

        user = self.get_email_owner(email)
        created = False
        if user is None:
            email = CustomUserManager.normalize_email(email)
            user = self.model(email=email)
            if password:
                auto_generated = False
            else:
                auto_generated = True
                user.password_change = True
                password = self.make_random_password(length=8)
            user.set_password(password)
            user.is_active = False
            user.gravatar = 'none'
            user.save(using=self._db)
            user.make_guid()
            created = True
        return user, created

    def create_user(self, **kwargs):
        """
        Creates an already activated user.

        """
        email = kwargs['email']
        password = kwargs['password1']
        if not email:
            raise ValueError('Email address required.')
        user = self.model(email=CustomUserManager.normalize_email(email))
        user.is_active = True
        user.gravatar = 'none'
        user.set_password(password)
        user.save(using=self._db)
        user.make_guid()
        return user

    def create_superuser(self, **kwargs):
        email = kwargs['email']
        password = kwargs['password']
        if not email:
            raise ValueError('Email address required.')
        u = self.model(email=CustomUserManager.normalize_email(email))
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.gravatar = u.email
        u.set_password(password)
        u.save(using=self._db)
        u.make_guid()
        return u


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name=_("email address"),
                              max_length=255, unique=True, db_index=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    gravatar = models.EmailField(verbose_name=_("gravatar email"),
                                 max_length=255, db_index=True, blank=True,
                                 null=True)

    profile_completion = models.IntegerField(validators=[MaxValueValidator(100),
                                                         MinValueValidator(0)],
                                             blank=False, default=0)

    # Permission Levels
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_("Designates whether the user can " + \
                                               "log into this admin site."))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_("Designates whether this user " + \
                                                "should be treated as active. " + \
                                                "Unselect this instead of deleting accounts."))
    is_disabled = models.BooleanField(_('disabled'), default=False)

    # Communication Settings

    # opt_in_myjobs is current hidden on the top level, refer to forms.py
    opt_in_myjobs = models.BooleanField(_('Opt-in to non-account emails and Saved Search:'),
                                        default=True,
                                        help_text=_('Checking this enables my.jobs\
                                                    to send email updates to you.'))

    opt_in_employers = models.BooleanField(_('Email is visible to Employers:'),
                                           default=True,
                                           help_text=_("Employers can message me."))

    last_response = models.DateField(default=datetime.datetime.now, blank=True)

    # Password Settings
    password_change = models.BooleanField(_('Password must be changed on next \
                                            login'), default=False)

    user_guid = models.CharField(max_length=100, db_index=True, unique=True)

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def __unicode__(self):
        return self.email

    def get_short_name(self):
        return self.email

    def make_guid(self):
        """
        Creates a uuid for the User only if the User does not currently has
        a user_guid.  After the uuid is made it is checked to make sure there
        are no duplicates. If no duplicates, save the GUID.
        """
        if not self.user_guid:
            self.user_guid = uuid.uuid4().hex
            if User.objects.filter(user_guid=self.user_guid):
                self.make_guid()
            self.save()
