import React from 'react';
import AsyncView from './asyncView';
import {t} from '../locale';
import PluginConfig from '../components/pluginConfig';
import ExternalLink from '../components/externalLink';
import IndicatorStore from '../stores/indicatorStore';

export default class ProjectPlugins extends AsyncView {
  getTitle() {
    let {plugin} = this.state;
    if (plugin && plugin.name) {
      return plugin.name;
    } else {
      return 'Sentry';
    }
  }

  getEndpoints() {
    let {projectId, orgId, pluginId} = this.props.params;
    return [['plugin', `/projects/${orgId}/${projectId}/plugins/${pluginId}/`]];
  }

  trimSchema(value) {
    return value.split('//')[1];
  }

  resetConfiguration() {
    let {projectId, orgId, pluginId} = this.props.params;
    let loadingIndicator = IndicatorStore.add(t('Saving changes..'));
    this.api.request(`/projects/${orgId}/${projectId}/plugins/${pluginId}/reset/`, {
      method: 'POST',
      success: plugin => {
        this.setState({plugin});
      },

      complete: () => IndicatorStore.remove(loadingIndicator),
    });
  }

  enable() {
    this.toggleEnable(true);
  }

  disable() {
    this.toggleEnable(false);
  }

  handleDisable() {
    this.setState({plugin: Object.assign({}, this.state.plugin, {enabled: false})});
  }

  toggleEnable(shouldEnable) {
    let method = shouldEnable ? 'POST' : 'DELETE';

    let {orgId, projectId, pluginId} = this.props.params;

    let loadingIndicator = IndicatorStore.add(t('Saving changes..'));

    this.api.request(`/projects/${orgId}/${projectId}/plugins/${pluginId}/`, {
      method,
      success: () => {
        this.setState({
          plugin: Object.assign({}, this.state.plugin, {enabled: shouldEnable}),
        });
      },
      complete: () => IndicatorStore.remove(loadingIndicator),
    });
  }

  renderActions() {
    let {plugin} = this.state;

    let reset = (
      <button
        type="submit"
        className="btn btn-default"
        onClick={() => this.resetConfiguration()}
      >
        {t('Reset Configuration')}
      </button>
    );

    let enable = (
      <button
        type="submit"
        className="btn btn-default"
        onClick={() => this.enable()}
        style={{marginRight: '6px'}}
      >
        {t('Enable Plugin')}
      </button>
    );

    let disable = (
      <button
        type="submit"
        className="btn btn-danger"
        onClick={() => this.disable()}
        style={{marginRight: '6px'}}
      >
        {t('Disable Plugin')}
      </button>
    );

    let toggleEnable = plugin.enabled ? disable : enable;

    return (
      <div className="pull-right">
        {plugin.canDisable && toggleEnable}
        {reset}
      </div>
    );
  }

  renderBody() {
    let {organization, project} = this.props;
    let {plugin} = this.state;

    return (
      <div>
        {this.renderActions()}
        <h2>{plugin.name}</h2>
        <hr />
        <div className="row">
          <div className="col-md-7">
            <PluginConfig
              organization={organization}
              project={project}
              data={plugin}
              onDisablePlugin={() => this.handleDisable()}
            />
          </div>
          <div className="col-md-4 col-md-offset-1">
            <div className="plugin-meta">
              <h4>Plugin Information</h4>

              <dl className="flat">
                <dt>Name:</dt>
                <dd>{plugin.name}</dd>
                <dt>Author</dt>
                <dd>{plugin.author.name}</dd>
                {plugin.author.url && (
                  <div>
                    <dt>URL</dt>
                    <dd>
                      <ExternalLink href={plugin.author.url}>
                        {this.trimSchema(plugin.author.url)}
                      </ExternalLink>
                    </dd>
                  </div>
                )}
                <dt>Version</dt>
                <dd>{plugin.version}</dd>
              </dl>

              {plugin.description && (
                <div>
                  <h4>Description</h4>
                  <p className="description">{plugin.description}</p>
                </div>
              )}

              {plugin.resourceLinks && (
                <div>
                  <h4>Resources</h4>
                  <dl className="flat">
                    {plugin.resourceLinks.map(({title, url}) => (
                      <dd key={url}>
                        <ExternalLink href={url}>{title}</ExternalLink>
                      </dd>
                    ))}
                  </dl>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
}
