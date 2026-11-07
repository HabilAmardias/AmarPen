<script lang="ts">
  import { onMount } from 'svelte';
  import { CheckCircle, Plug, Plus, ShieldCheck, XCircle } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';
  import type { McpServerSummary } from '../../../../lib/api/types';
  import ErrorView from '../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../../lib/components/StatusBadge.svelte';

  let servers: McpServerSummary[] = [];
  let ready: { ready: boolean; checks: Array<{ name: string; passed: boolean; blocking: boolean; message: string }> } | null = null;
  let loading = true;
  let pending = '';
  let stableId = '';
  let endpoint = '';
  let protocol = '2026-07-28';
  let error = '';
  let notice = '';

  async function load() {
    loading = true;
    error = '';
    try {
      servers = (await api.admin.mcpServers()).items;
      ready = await api.admin.mcpReady();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load MCP registry';
    } finally {
      loading = false;
    }
  }

  async function discover(server: McpServerSummary) {
    pending = server.stable_id;
    error = '';
    notice = '';
    try {
      const manifest = await api.admin.discoverMcpServer(server.stable_id);
      notice = `Discovery created manifest v${manifest.version}. Review and activate it explicitly.`;
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'MCP discovery failed';
    } finally {
      pending = '';
    }
  }

  async function createServer() {
    pending = 'create';
    error = '';
    notice = '';
    try {
      await api.admin.createMcpServer({
        stable_id: stableId,
        endpoint,
        transport: 'streamable_http',
        protocol_revision: protocol,
        implementation_version: '2.3.0',
        enabled: true
      });
      stableId = '';
      endpoint = '';
      notice = 'MCP server registered. Run discovery and validate the manifest.';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to create MCP server';
    } finally {
      pending = '';
    }
  }

  async function validateManifest(manifestId: string) {
    pending = manifestId;
    error = '';
    notice = '';
    try {
      await api.admin.validateMcpManifest(manifestId);
      notice = 'Manifest validation recorded.';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Manifest validation failed';
    } finally {
      pending = '';
    }
  }

  async function revokeServer(server: McpServerSummary) {
    if (!confirm(`Revoke ${server.stable_id}? Affected runs will pause.`)) return;
    pending = server.stable_id;
    error = '';
    notice = '';
    try {
      await api.admin.revokeMcpServer(server.stable_id, 'Administrator revocation');
      notice = 'MCP server revoked. Affected runs were paused.';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Server revocation failed';
    } finally {
      pending = '';
    }
  }

  async function revokeManifest(manifestId: string) {
    if (!confirm('Revoke this manifest? Affected runs will pause.')) return;
    pending = manifestId;
    error = '';
    notice = '';
    try {
      await api.admin.revokeMcpManifest(manifestId, 'Administrator revocation');
      notice = 'MCP manifest revoked. Affected runs were paused.';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Manifest revocation failed';
    } finally {
      pending = '';
    }
  }

  async function activate(manifestId: string) {
    pending = manifestId;
    error = '';
    notice = '';
    try {
      await api.admin.activateMcpManifest(manifestId);
      notice = 'MCP manifest activated. Active runs retain their pinned manifest.';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'MCP manifest activation failed';
    } finally {
      pending = '';
    }
  }

  onMount(load);
</script>

<svelte:head><title>MCP registry | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="alert">
    <ShieldCheck size={16} aria-hidden="true" />
    MCP servers and tool manifests are Administrator-managed. Runs pin the active manifest; discovery never grants execution permission.
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}
  {#if notice}<div class="alert success" role="status">{notice}</div>{/if}

  <form class="card stack" on:submit|preventDefault={createServer}>
    <div class="row" style="justify-content: space-between;">
      <span class="panel-kicker">REGISTER MCP SERVER</span>
      <Plus size={17} aria-hidden="true" class="text-green" />
    </div>
    <div class="grid three">
      <label>Stable ID <input bind:value={stableId} required /></label>
      <label>Endpoint <input bind:value={endpoint} placeholder="https://mcp-server:8443/mcp" required /></label>
      <label>Protocol revision <input bind:value={protocol} required /></label>
    </div>
    <button type="submit" disabled={pending === 'create'}>{pending === 'create' ? 'Registering…' : 'Register server'}</button>
  </form>

  {#if ready}
    <div class="card stack">
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">MCP READINESS</span>
        <Plug size={17} aria-hidden="true" class="text-cyan" />
      </div>
      <StatusBadge value={ready.ready ? 'PASSED' : 'BLOCKED'} label={ready.ready ? 'Ready' : 'Blocked'} />
      <ul class="data-list">
        {#each ready.checks as check}
          <li><span>{check.name.replaceAll('_', ' ')}</span><strong class:text-green={check.passed} class:text-danger={!check.passed}>{check.passed ? 'OK' : 'FAIL'}</strong></li>
        {/each}
      </ul>
    </div>
  {/if}

  {#if loading}
    <LoadingState label="Loading MCP registry" />
  {:else if error && servers.length === 0}
    <ErrorView title="Could not load MCP registry" message={error} onretry={load} />
  {:else}
    {#each servers as server (server.id)}
      <section class="card stack">
        <div class="row" style="justify-content: space-between;">
          <div>
            <span class="panel-kicker">MCP SERVER</span>
            <h2>{server.stable_id}</h2>
            <p class="small muted">{server.endpoint} · {server.transport} · protocol {server.protocol_revision || 'unset'} · SDK {server.implementation_version || 'unset'}</p>
          </div>
          <StatusBadge value={server.enabled ? 'ACTIVE' : 'DISABLED'} />
        </div>
        <div class="row">
          <button type="button" class="secondary" disabled={pending === server.stable_id} on:click={() => discover(server)}>
            {pending === server.stable_id ? 'Discovering…' : 'Refresh discovery'}
          </button>
          <button type="button" class="danger" disabled={pending === server.stable_id} on:click={() => revokeServer(server)}>
            <XCircle size={13} aria-hidden="true" /> Revoke server
          </button>
        </div>
        {#if server.manifests.length === 0}
          <p class="muted">No manifest recorded. Run discovery and activate a reviewed manifest.</p>
        {:else}
          <table>
            <caption class="sr-only">MCP manifests</caption>
            <thead><tr><th scope="col">Version</th><th scope="col">State</th><th scope="col">Tools</th><th scope="col">Hash</th><th scope="col">Action</th></tr></thead>
            <tbody>
              {#each server.manifests as manifest (manifest.id)}
                <tr>
                  <td>v{manifest.version}</td>
                  <td><StatusBadge value={manifest.state} /></td>
                  <td>{manifest.tool_count}</td>
                  <td class="small muted">{manifest.integrity_hash.slice(0, 16)}…</td>
                  <td>
                    <div class="row">
                      <button type="button" class="secondary" disabled={pending === manifest.id || manifest.state === 'REVOKED'} on:click={() => validateManifest(manifest.id)}>Validate</button>
                      <button type="button" class="secondary" disabled={manifest.state === 'ACTIVE' || pending === manifest.id} on:click={() => activate(manifest.id)}>
                        <CheckCircle size={13} aria-hidden="true" /> Activate
                      </button>
                      <button type="button" class="danger" disabled={manifest.state === 'REVOKED' || pending === manifest.id} on:click={() => revokeManifest(manifest.id)}>
                        <XCircle size={13} aria-hidden="true" /> Revoke
                      </button>
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </section>
    {/each}
  {/if}
</div>
