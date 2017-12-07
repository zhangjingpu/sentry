from __future__ import absolute_import

from sentry.integrations import Integration
from sentry.utils.pipeline import NestedPipelineView
from sentry.identity.pipeline import IdentityProviderPipeline
from sentry.utils.http import absolute_uri


class SlackIntegration(Integration):
    key = 'slack'
    name = 'Slack'

    # TODO: Remove id and use key everywhere for integrations
    key = 'slack'

    identity_oauth_scopes = (
        'bot',
        'chat:write:bot',
        'commands',
        'links:read',
        'links:write',
        'team:read',
    )

    def get_pipeline(self):
        identity_pipeline_config = {
            'oauth_scopes': self.identity_oauth_scopes,
            'redirect_url': absolute_uri('/extensions/slack/setup/'),
        }

        identity_pipeline = NestedPipelineView(
            bind_key='identity',
            provider_key='slack',
            pipeline_cls=IdentityProviderPipeline,
            config=identity_pipeline_config,
        )

        return [identity_pipeline]

    def build_integration(self, state):
        data = state['identity']['data']
        assert data['ok']

        return {
            'name': data['team_name'],
            'external_id': data['team_id'],
            'metadata': {
                'access_token': data['access_token'],
                'bot_access_token': data['bot']['bot_access_token'],
                'bot_user_id': data['bot']['bot_user_id'],
            },
            'user_identity': {
                'type': 'slack',
                'external_id': data['user_id'],
                'scopes': sorted(data['scope'].split(',')),
                'data': {
                    'access_token': data['access_token'],
                },
            },
        }
