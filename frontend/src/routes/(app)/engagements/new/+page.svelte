<script lang="ts">
  import { goto } from '$app/navigation';
  import { ArrowLeft, Crosshair, ShieldCheck } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';

  const attestationText =
    'I confirm I own this target or am explicitly authorized to test it. I understand the scan may create test accounts and send state-changing requests within the recorded scope.';

  let baseUrl = '';
  let attested = false;
  let error = '';
  let pending = false;

  async function submit() {
    error = '';
    if (!attested) {
      error = 'Authorization attestation is required.';
      return;
    }
    pending = true;
    try {
      const engagement = await api.engagements.quickStart({
        base_url: baseUrl,
        authorization_attested: true
      });
      await goto(`/engagements/${engagement.id}`);
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to create engagement';
    } finally {
      pending = false;
    }
  }
</script>

<svelte:head><title>New engagement | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="operation-header">
    <div>
      <span class="panel-kicker">OPERATION SETUP</span>
      <h1>Authorize operation</h1>
      <p class="muted">Provide the base URL and record the authorization attestation. Scope, window, budgets, and model profile are prepared automatically.</p>
    </div>
    <a class="button secondary" href="/dashboard"><ArrowLeft size={14} aria-hidden="true" /> Cancel</a>
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}

  <form class="card stack" on:submit|preventDefault={submit}>
    <label>
      Base URL
      <input bind:value={baseUrl} required placeholder="https://api.example.com" autocomplete="url" />
    </label>
    <p class="small muted">The host becomes the approved scope. Discovered links and endpoints cannot expand it.</p>

    <div class="alert warning">
      <ShieldCheck size={17} aria-hidden="true" />
      <div>
        <strong>Authorization attestation</strong>
        <span>This action is recorded with your user, timestamp, scope hash, and source address.</span>
      </div>
    </div>

    <label class="checkbox attestation">
      <input type="checkbox" bind:checked={attested} required />
      <span>{attestationText}</span>
    </label>

    <div class="row form-actions">
      <button type="submit" disabled={pending || !attested || !baseUrl.trim()}>
        <Crosshair size={15} weight="bold" aria-hidden="true" />
        {pending ? 'Authorizing…' : 'Authorize and create'}
      </button>
      <a class="button secondary" href="/dashboard">Cancel</a>
    </div>
  </form>
</div>

<style>
  .attestation {
    align-items: flex-start;
    line-height: 1.5;
  }

  .attestation input {
    margin-top: 0.25rem;
  }

  .form-actions {
    justify-content: flex-end;
  }
</style>
