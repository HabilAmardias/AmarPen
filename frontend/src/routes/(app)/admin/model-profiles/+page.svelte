<script lang="ts">
  import { onMount } from 'svelte';
  import { Cpu, Globe, HardDrives, LockKey, Plus, ShieldCheck, WifiHigh } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';
  import type { ModelProfile } from '../../../../lib/api/types';
  import ErrorView from '../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../../lib/components/StatusBadge.svelte';

  let profiles: ModelProfile[] = [];
  let health: { status: string; checks: Record<string, boolean> } | null = null;
  let name = '';
  let baseUrl = 'http://localhost:8080/v1';
  let model = 'mock-pentest';
  let dataBoundary = 'on_premises';
  let apiKey = '';
  let capabilities = ['chat', 'structured_outputs'];
  let loading = true;
  let error = '';
  let notice = '';
  let testingId = '';
  let editingKeyId = '';
  let newApiKey = '';
  let savingKey = false;

  async function load() {
    loading = true;
    error = '';
    try {
      profiles = (await api.admin.modelProfiles()).items;
      health = await api.admin.health();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load model profiles';
    } finally {
      loading = false;
    }
  }

  function detail(profile: ModelProfile, key: string): string {
    const value = profile.last_test_detail?.[key];
    if (typeof value === 'boolean') return value ? 'OK' : 'FAIL';
    if (value === undefined || value === null || value === '') return '—';
    return String(value);
  }

  async function testProfile(profile: ModelProfile) {
    testingId = profile.id;
    error = '';
    notice = '';
    try {
      const result = await api.admin.testModelProfile(profile.id);
      notice = `Connection test: ${result.last_test_status}`;
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Connection test failed';
    } finally {
      testingId = '';
    }
  }

  async function createProfile() {
    error = '';
    notice = '';
    try {
      const profile = await api.admin.createModelProfile({
        name,
        base_url: baseUrl,
        model,
        data_boundary: dataBoundary,
        api_key: apiKey,
        capabilities,
        enabled: true
      });
      name = '';
      apiKey = '';
      notice = `Profile created. Connection test: ${profile.last_test_status}`;
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to create model profile';
    }
  }

  function editKey(profile: ModelProfile) {
    editingKeyId = profile.id;
    newApiKey = '';
    error = '';
    notice = '';
  }

  function cancelEditKey() {
    editingKeyId = '';
    newApiKey = '';
  }

  async function updateKey(profile: ModelProfile) {
    if (!newApiKey.trim()) return;
    savingKey = true;
    error = '';
    notice = '';
    try {
      const updated = await api.admin.updateModelProfile(profile.id, { api_key: newApiKey });
      notice = `API key updated. Connection test: ${updated.last_test_status}`;
      editingKeyId = '';
      newApiKey = '';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to update API key';
    } finally {
      savingKey = false;
    }
  }

  onMount(load);
</script>

<svelte:head><title>Model profiles | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="alert">
    <ShieldCheck size={16} aria-hidden="true" />
    Cloud inference is explicit. No automatic local-to-cloud fallback is permitted.
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}
  {#if notice}<div class="alert success" role="status">{notice}</div>{/if}

  <div class="grid two">
    <form class="card stack" on:submit|preventDefault={createProfile}>
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">ADD PROFILE</span>
        <Plus size={17} aria-hidden="true" class="text-green" />
      </div>
      <div class="grid two">
        <label>Name <input bind:value={name} required /></label>
        <label>Model identifier <input bind:value={model} required /></label>
      </div>
      <label>Base URL <input bind:value={baseUrl} required /></label>
      <label>
        Data boundary
        <select bind:value={dataBoundary}>
          <option value="on_premises">On-premises</option>
          <option value="approved_cloud">Approved cloud</option>
        </select>
      </label>
      <label>
        API key
        <input
          type="password"
          aria-label="API key"
          bind:value={apiKey}
          required={dataBoundary === 'approved_cloud'}
          autocomplete="new-password"
          spellcheck="false"
          placeholder={dataBoundary === 'approved_cloud' ? 'Required for cloud endpoints' : 'Optional bearer credential'}
        />
        <span class="small muted">Sent as <code>Authorization: Bearer …</code>. Stored encrypted and never returned.</span>
      </label>
      <fieldset class="capability-fieldset">
        <legend>Declared capabilities</legend>
        <label class="checkbox"><input type="checkbox" bind:group={capabilities} value="chat" /> Chat completions</label>
        <label class="checkbox"><input type="checkbox" bind:group={capabilities} value="structured_outputs" /> Structured outputs</label>
        <label class="checkbox"><input type="checkbox" bind:group={capabilities} value="tools" /> Tool calling</label>
        <p class="small muted">Agentic runs require a latest probe result with verified structured outputs.</p>
      </fieldset>
      <button type="submit"><Cpu size={14} weight="bold" aria-hidden="true" /> Create profile</button>
    </form>

    <div class="card stack health-panel">
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">PLATFORM HEALTH</span>
        <Cpu size={17} aria-hidden="true" class="text-cyan" />
      </div>
      {#if health}
        <div class="health-status">
          <span class="status-orb" aria-hidden="true"></span>
          <span>Platform health: <StatusBadge value={health.status === 'ok' ? 'PASSED' : 'WARNING'} label={health.status} /></span>
        </div>
        <ul class="data-list">
          {#each Object.entries(health.checks) as [check, passed]}
            <li><span>{check.replaceAll('_', ' ')}</span><strong class:text-green={passed} class:text-danger={!passed}>{passed ? 'OK' : 'FAIL'}</strong></li>
          {/each}
        </ul>
      {:else}
        <LoadingState label="Checking platform health" />
      {/if}
      <div class="boundary-note">
        <HardDrives size={15} aria-hidden="true" />
        <span>Local evidence and platform state remain on premises.</span>
      </div>
    </div>
  </div>

  {#if loading}
    <LoadingState label="Loading model profiles" />
  {:else if error && profiles.length === 0}
    <ErrorView title="Could not load model profiles" message={error} onretry={load} />
  {:else}
    <div class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 0.5rem;">
        <span class="panel-kicker">MODEL PROFILES</span>
        <span class="hud-meta"><span>{profiles.length} PROFILES</span></span>
      </div>
      <table>
        <caption class="sr-only">Model profiles</caption>
        <thead><tr><th scope="col">Name</th><th scope="col">Model</th><th scope="col">Boundary</th><th scope="col">Credentials</th><th scope="col">State</th><th scope="col">Connection</th><th scope="col">Action</th></tr></thead>
        <tbody>
          {#each profiles as profile (profile.id)}
            <tr>
              <td><span class="profile-name">{profile.name}</span></td>
              <td>{profile.model}</td>
              <td>
                <span class="boundary-tag">
                  {#if profile.data_boundary === 'on_premises'}<HardDrives size={12} aria-hidden="true" />{:else}<Globe size={12} aria-hidden="true" />{/if}
                  {profile.data_boundary.replaceAll('_', ' ')}
                </span>
              </td>
              <td>
                {#if profile.credential_source === 'stored'}
                  <span class="credential-tag"><LockKey size={12} aria-hidden="true" /> API key</span>
                {:else if profile.credential_source === 'environment'}
                  <span class="credential-tag"><LockKey size={12} aria-hidden="true" /> Environment</span>
                {:else}
                  <span class="small muted">No credential</span>
                {/if}
              </td>
              <td><StatusBadge value={profile.enabled ? 'ACTIVE' : 'DISABLED'} /></td>
              <td>
                <div class="connection-cell">
                  <StatusBadge value={profile.last_test_status || 'UNKNOWN'} label={profile.last_test_status || 'Not tested'} />
                  <StatusBadge value={profile.last_test_detail?.structured_outputs ? 'PASSED' : 'BLOCKED'} label={profile.last_test_detail?.structured_outputs ? 'Agent-ready' : 'Not agent-ready'} />
                  {#if profile.last_tested_at}<span class="small muted">{new Date(profile.last_tested_at).toLocaleString()}</span>{/if}
                  {#if profile.last_test_status === 'REACHABLE'}
                    <span class="small muted">chat {detail(profile, 'chat_ok')} / structured {detail(profile, 'structured_outputs')} / {detail(profile, 'latency_ms')}ms</span>
                  {:else if profile.last_test_detail?.error}
                    <span class="small error-text">{detail(profile, 'error')}</span>
                  {/if}
                </div>
              </td>
              <td>
                <div class="row action-row">
                  <button type="button" class="secondary" disabled={testingId === profile.id} on:click={() => testProfile(profile)}>
                    <WifiHigh size={13} aria-hidden="true" />
                    {testingId === profile.id ? 'Testing…' : 'Test connection'}
                  </button>
                  <button type="button" class="secondary" on:click={() => editKey(profile)}>
                    <LockKey size={13} aria-hidden="true" />
                    {profile.has_api_key ? 'Update key' : 'Add key'}
                  </button>
                </div>
              </td>
            </tr>
            {#if editingKeyId === profile.id}
              <tr class="key-editor">
                <td colspan="7">
                  <form class="key-form" on:submit|preventDefault={() => updateKey(profile)}>
                    <label>
                      New API key for {profile.name}
                      <input
                        type="password"
                        bind:value={newApiKey}
                        required
                        autocomplete="new-password"
                        spellcheck="false"
                        placeholder="Enter a replacement bearer token"
                      />
                    </label>
                    <button type="submit" disabled={savingKey || !newApiKey.trim()}>
                      {savingKey ? 'Saving…' : 'Save API key'}
                    </button>
                    <button type="button" class="secondary" on:click={cancelEditKey}>Cancel</button>
                  </form>
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .health-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.82rem;
  }

  .boundary-note {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    color: var(--text-muted);
    font-size: 0.76rem;
  }

  .profile-name {
    color: var(--primary);
  }

  .boundary-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    color: var(--cyan);
    font-size: 0.72rem;
    text-transform: uppercase;
  }

  .connection-cell {
    display: grid;
    gap: 0.2rem;
    min-width: 10rem;
  }

  .credential-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    color: var(--cyan);
    font-size: 0.72rem;
    text-transform: uppercase;
  }

  .action-row {
    gap: 0.35rem;
    flex-wrap: wrap;
  }

  .key-editor {
    background: rgba(57, 255, 136, 0.03);
  }

  .key-form {
    display: flex;
    flex-wrap: wrap;
    align-items: end;
    gap: 0.55rem;
    padding: 0.35rem 0;
  }

  .key-form label {
    flex: 1 1 18rem;
  }

  .key-form button {
    flex: 0 0 auto;
  }

  code {
    color: var(--cyan);
  }

  .capability-fieldset {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 0.9rem;
    border: 1px solid var(--border);
    padding: 0.65rem;
  }

  .capability-fieldset legend {
    padding: 0 0.3rem;
  }

  .capability-fieldset .checkbox {
    width: auto;
  }

  .error-text {
    color: var(--danger);
  }
</style>
