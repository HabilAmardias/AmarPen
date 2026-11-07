<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { ArrowLeft, Crosshair, ShieldWarning } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../../lib/api/client';
  import type { Engagement, ModelProfileOption } from '../../../../../lib/api/types';
  import ErrorView from '../../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../../lib/components/LoadingState.svelte';

  export let data: { id: string };

  let engagement: Engagement | null = null;
  let modelProfiles: ModelProfileOption[] = [];
  let loading = true;
  let pending = false;
  let error = '';

  let name = '';
  let description = '';
  let authorizationRef = '';
  let authorizationValid = false;
  let targets = '';
  let exclusions = '';
  let windowStart = '';
  let windowEnd = '';
  let modelProfile = '';
  let businessContext = '';
  let expectedVersion = 1;

  function toLocalInput(value: string | null): string {
    if (!value) return '';
    const date = new Date(value);
    const pad = (part: number) => String(part).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  }

  async function load() {
    loading = true;
    error = '';
    try {
      const [current, options] = await Promise.all([
        api.engagements.get(data.id),
        api.modelProfiles.options()
      ]);
      engagement = current;
      modelProfiles = options.items;
      name = current.name;
      description = current.description;
      authorizationRef = current.authorization_ref;
      authorizationValid = current.authorization_valid;
      targets = current.targets.join('\n');
      exclusions = current.exclusions.join('\n');
      windowStart = toLocalInput(current.window_start);
      windowEnd = toLocalInput(current.window_end);
      modelProfile = modelProfiles.some((profile) => profile.name === current.model_profile) ? current.model_profile : '';
      businessContext = String(current.business_context?.statement ?? '');
      expectedVersion = current.config_version;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load engagement';
    } finally {
      loading = false;
    }
  }

  async function submit() {
    if (!engagement) return;
    pending = true;
    error = '';
    try {
      await api.engagements.update(engagement.id, {
        name,
        description,
        authorization_ref: authorizationRef,
        authorization_valid: authorizationValid,
        targets: targets.split('\n').map((value) => value.trim()).filter(Boolean),
        exclusions: exclusions.split('\n').map((value) => value.trim()).filter(Boolean),
        window_start: windowStart ? new Date(windowStart).toISOString() : null,
        window_end: windowEnd ? new Date(windowEnd).toISOString() : null,
        access_profile: engagement.access_profile,
        model_profile: modelProfile,
        budgets: engagement.budgets,
        prohibited: engagement.prohibited,
        business_context: businessContext ? { ...engagement.business_context, statement: businessContext } : engagement.business_context,
        risk_policy_id: engagement.risk_policy_id,
        expected_version: expectedVersion
      });
      await goto(`/engagements/${engagement.id}`);
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to update engagement';
    } finally {
      pending = false;
    }
  }

  onMount(load);
</script>

<svelte:head><title>Edit engagement | AI-Assisted Pentest</title></svelte:head>

{#if loading}
  <LoadingState label="Loading engagement configuration" />
{:else if error && !engagement}
  <ErrorView title="Engagement unavailable" message={error} onretry={load} />
{:else if engagement}
  <div class="stack">
    <div class="operation-header">
      <div>
        <span class="panel-kicker">ENGAGEMENT CONFIGURATION</span>
        <h1>Edit Operation</h1>
        <p class="muted">Correct authorization, scope, testing window, or model selection before starting a run.</p>
      </div>
      <a class="button secondary" href={`/engagements/${engagement.id}`}><ArrowLeft size={14} aria-hidden="true" /> Cancel</a>
    </div>

    {#if error}<div class="alert error" role="alert">{error}</div>{/if}

    <div class="alert warning scope-warning">
      <ShieldWarning size={18} weight="bold" aria-hidden="true" />
      <div>
        <strong>Authorization remains a separate control.</strong>
        <span>Record the real approval reference and confirm validity; the platform will not infer authorization from scope.</span>
      </div>
    </div>

    <form class="stack" on:submit|preventDefault={submit}>
      <div class="grid two">
        <section class="card stack">
          <span class="panel-kicker">IDENTITY + AUTHORIZATION</span>
          <label>Engagement name <input bind:value={name} required minlength="3" /></label>
          <label>Description <input bind:value={description} /></label>
          <label>Authorization reference <input bind:value={authorizationRef} required /></label>
          <label class="checkbox">
            <input type="checkbox" bind:checked={authorizationValid} />
            Authorization is recorded and valid
          </label>
          {#if !authorizationRef || !authorizationValid}
            <p class="alert error" role="status">Readiness remains blocked until the reference is recorded and the authorization is confirmed.</p>
          {/if}
          <div class="grid two">
            <label>Testing window start <input type="datetime-local" bind:value={windowStart} /></label>
            <label>Testing window end <input type="datetime-local" bind:value={windowEnd} /></label>
          </div>
        </section>

        <section class="card stack">
          <span class="panel-kicker">TARGET SURFACE + MODEL</span>
          <label>Approved targets (one per line) <textarea bind:value={targets} required></textarea></label>
          <label>Exclusions (one per line) <textarea bind:value={exclusions}></textarea></label>
          <label>
            Model profile
            <select bind:value={modelProfile} required>
              <option value="" disabled>Select an enabled profile</option>
              {#each modelProfiles as profile}
                <option value={profile.name}>{profile.name} / {profile.model} / {profile.last_test_status || 'not tested'}</option>
              {/each}
            </select>
          </label>
          {#if modelProfiles.length === 0}
            <p class="alert warning" role="status">No enabled model profiles are available. Ask an administrator to add and test one.</p>
          {:else if !modelProfile}
            <p class="alert warning" role="status">The previously selected profile is unavailable. Select an enabled replacement.</p>
          {/if}
          <label>Business context <input bind:value={businessContext} placeholder="Risk owner and critical workflows" /></label>
        </section>
      </div>

      <div class="row form-actions">
        <button type="submit" disabled={pending || !modelProfile || modelProfiles.length === 0}>
          <Crosshair size={15} weight="bold" aria-hidden="true" />
          {pending ? 'Saving…' : 'Save changes'}
        </button>
        <a class="button secondary" href={`/engagements/${engagement.id}`}>Cancel</a>
      </div>
    </form>
  </div>
{/if}

<style>
  .scope-warning {
    display: flex;
    align-items: flex-start;
    gap: 0.65rem;
  }

  .scope-warning strong {
    display: block;
  }

  .scope-warning span {
    color: var(--text-muted);
    font-size: 0.84rem;
  }

  .checkbox {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
  }

  .checkbox input {
    width: auto;
  }

  .form-actions {
    justify-content: flex-end;
  }
</style>
