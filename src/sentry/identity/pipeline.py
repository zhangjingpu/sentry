from __future__ import absolute_import, print_function

import logging

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sentry.utils.pipeline import Pipeline
from sentry.models import Identity, IdentityStatus

from . import default_manager

IDENTITY_LINKED = _("Your {identity_provider} account has been associated with your Sentry account")

logger = logging.getLogger('sentry.identity')


class IdentityProviderPipeline(Pipeline):
    logger = logger

    pipeline_name = 'identity_provider'
    provider_manager = default_manager

    def redirect_url(self):
        associate_url = reverse('sentry-account-associate-identity', args=[
            self.organization.slug,
            self.provider.key,
        ])

        # Use configured redirect_url if specified for the pipeline if available
        return self.config.get('redirect_url', associate_url)

    def finish_pipeline(self):
        identity = self.provider.build_identity(self.state.data)

        defaults = {
            'status': IdentityStatus.VALID,
            'scopes': identity['scopes'],
            'data': identity['data'],
            'date_verified': timezone.now(),
        }

        identity, created = Identity.objects.get_or_create(
            idp=self.provider_model,
            user=self.request.user,
            external_id=identity['external_id'],
            defaults=defaults,
        )

        if not created:
            identity.update(**defaults)

        messages.add_message(self.request, messages.SUCCESS, IDENTITY_LINKED.format(
            identity_provider=self.provider.name,
        ))

        self.state.clear()

        return HttpResponseRedirect(reverse('sentry-account-settings-identities'))
