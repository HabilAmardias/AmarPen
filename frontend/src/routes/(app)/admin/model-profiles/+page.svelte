<script lang="ts">
  import { onMount } from 'svelte';
  import { Cpu, Globe, HardDrives, Plus, ShieldCheck } from 'phosphor-svelte';
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
  let loading = true;
  let error = '';

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

  async function createProfile() {
    error = '';
    try {
      await api.admin.createModelProfile({
        name,
        base_url: baseUrl,
        model,
        data_boundary: dataBoundary,
        capabilities: ['chat', 'structured_outputs'],
        enabled: true
      });
      name = '';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to create model profile';
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
        <thead><tr><th scope="col">Name</th><th scope="col">Model</th><th scope="col">Boundary</th><th scope="col">State</th></tr></thead>
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
              <td><StatusBadge value={profile.enabled ? 'ACTIVE' : 'DISABLED'} /></td>
            </tr>
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
</style>
