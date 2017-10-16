from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.response import Response

from sentry import features
from sentry.api.bases.organization import OrganizationEndpoint, OrganizationAuthProviderPermission
from sentry.api.serializers import serialize
from sentry.models import AuthProvider, OrganizationMember
from sentry.utils.http import absolute_uri

ERR_NO_SSO = _('The SSO feature is not enabled for this organization.')


class OrganizationAuthProviderDetailsEndpoint(OrganizationEndpoint):
    permission_classes = (OrganizationAuthProviderPermission, )

    def get(self, request, organization):
        """
        Retrieve an Organization's Auth Provider
        ````````````````````````````````````````

        :pparam string organization_slug: the organization short name
        :auth: required
        """
        if not features.has('organizations:sso', organization, actor=request.user):
            return Response(ERR_NO_SSO, status=status.HTTP_403_FORBIDDEN)

        try:
            auth_provider = AuthProvider.objects.get(
                organization=organization,
            )
        except AuthProvider.DoesNotExist:
            # This is a valid state where org does not have an auth provider
            # configured, make sure we respond with a 20x
            return Response(status=status.HTTP_204_NO_CONTENT)

        provider = auth_provider.get_provider()

        pending_links_count = OrganizationMember.objects.filter(
            organization=organization,
            flags=~getattr(OrganizationMember.flags, 'sso:linked'),
        ).count()

        context = {
            'pending_links_count': pending_links_count,
            'login_url': absolute_uri(reverse('sentry-organization-home', args=[organization.slug])),
            'auth_provider': serialize(auth_provider),
            'default_role': organization.default_role,
            'require_link': not auth_provider.flags.allow_unlinked,
            'provider_name': provider.name,
        }

        return Response(serialize(context, request.user))
