from __future__ import absolute_import

from rest_framework.response import Response

from sentry.auth.access import SDKAccess
from sentry.api.authentication import (
    AuthenticationFailed, QuietBasicAuthentication
)
from sentry.api.bases.project import ProjectEndpoint, ProjectPermission
from sentry.api.exceptions import ResourceDoesNotExist
from sentry.app import raven
from sentry.models import Project, ProjectStatus


class SDKAuthentication(QuietBasicAuthentication):
    def authenticate(self, request):
        from sentry.coreapi import ClientApiHelper
        helper = ClientApiHelper(
            agent=request.META.get('HTTP_USER_AGENT'),
            ip_address=request.META['REMOTE_ADDR'],
        )
        try:
            client_auth = helper.auth_from_request(request)
        except Exception:
            return None

        try:
            project_id = helper.project_id_from_auth(client_auth)
        except Exception:
            raise AuthenticationFailed('Invalid credentials')

        access = SDKAccess(
            project_id=project_id,
        )

        return self.authenticate_credentials(access)

    def authenticate_credentials(self, access):
        return (None, access)


class SDKPermission(ProjectPermission):
    def has_object_permission(self, request, view, project):
        request.access = request.auth
        allowed_scopes = set(self.scope_map.get(request.method, []))
        return any(
            request.auth.has_project_scope(project, s)
            for s in allowed_scopes,
        )


class SDKProjectEndpoint(ProjectEndpoint):
    def convert_args(self, request, project_id, *args, **kwargs):
        try:
            project = Project.objects.filter(
                id=project_id,
            ).select_related('organization', 'team').get()
        except Project.DoesNotExist:
            raise ResourceDoesNotExist

        if project.status != ProjectStatus.VISIBLE:
            raise ResourceDoesNotExist

        project.team.organization = project.organization

        self.check_object_permissions(request, project)

        raven.tags_context({
            'project': project.id,
            'organization': project.organization_id,
        })

        kwargs['project'] = project
        return (args, kwargs)


class RelayConfigEndpoint(SDKProjectEndpoint):
    authentication_classes = (
        SDKAuthentication,
    )
    permission_classes = (
        SDKPermission,
    )

    def get(self, request, project):
        return Response({
            'hi': 'there',
        })
