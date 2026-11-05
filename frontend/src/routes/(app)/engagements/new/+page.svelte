<script lang="ts">
  import { goto } from '$app/navigation';
  import { ArrowLeft, Crosshair, ShieldWarning } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';

  let name = '';
  let authorizationRef = '';
  let authorizationValid = false;
  let targets = '';
  let exclusions = '';
  let windowStart = '';
  let windowEnd = '';
  let modelProfile = 'local-default';
  let businessContext = '';
  let error = '';
  let pending = false;

  async function submit() {
    error = '';
    pending = true;
    try {
      const engagement = await api.engagements.create({
        name,
        authorization_ref: authorizationRef,
        authorization_valid: authorizationValid,
        targets: targets.split('\n').map((value) => value.trim()).filter(Boolean),
        exclusions: exclusions.split('\n').map((value) => value.trim()).filter(Boolean),
        window_start: windowStart ? new Date(windowStart).toISOString() : null,
        window_end: windowEnd ? new Date(windowEnd).toISOString() : null,
        model_profile: modelProfile,
        business_context: businessContext ? { statement: businessContext } : {},
        access_profile: 'anonymous'
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
      <h1>Configure Operation</h1>
      <p class="muted">Authorization and scope are required. Discovered assets are not automatically in scope.</p>
    </div>
    <a class="button secondary" href="/dashboard"><ArrowLeft size={14} aria-hidden="true" /> Cancel</a>
  </div>

  <div class="alert warning scope-warning">
    <ShieldWarning size={18} weight="bold" aria-hidden="true" />
    <div>
      <strong>Scope is enforced by the backend.</strong>
      <span>Only recorded targets count as authorized. Redirects, shared hosting, and discovered domains do not expand scope.</span>
    </div>
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}

  <form class="stack" on:submit|preventDefault={submit}>
    <div class="grid two">
      <section class="card stack">
        <span class="panel-kicker">IDENTITY + AUTHORIZATION</span>
        <label>Engagement name <input name="name" bind:value={name} required minlength="3" /></label>
        <label>Authorization reference <input name="authorization_ref" bind:value={authorizationRef} required /></label>
        <label class="checkbox">
          <input name="authorization_valid" type="checkbox" bind:checked={authorizationValid} />
          Authorization is recorded and valid
        </label>
        <div class="grid two">
          <label>Testing window start <input name="window_start" type="datetime-local" bind:value={windowStart} /></label>
          <label>Testing window end <input name="window_end" type="datetime-local" bind:value={windowEnd} /></label>
        </div>
      </section>

      <section class="card stack">
        <span class="panel-kicker">TARGET SURFACE</span>
        <label>
          Approved targets (one per line)
          <textarea name="targets" bind:value={targets} required placeholder="example.com"></textarea>
        </label>
        <label>
          Exclusions (one per line)
          <textarea name="exclusions" bind:value={exclusions} placeholder="admin.example.com"></textarea>
        </label>
        <p class="small muted">Targets are normalized and checked against exclusions before every tool action.</p>
      </section>
    </div>

    <section class="card stack">
      <span class="panel-kicker">EXECUTION PROFILE</span>
      <div class="grid two">
        <label>Model profile <input name="model_profile" bind:value={modelProfile} /></label>
        <label>
          Business context
          <input name="business_context" bind:value={businessContext} placeholder="Risk owner and critical workflows" />
        </label>
      </div>
    </section>

    <div class="row form-actions">
      <button type="submit" disabled={pending}>
        <Crosshair size={15} weight="bold" aria-hidden="true" />
        {pending ? 'Creating…' : 'Create engagement'}
      </button>
      <a class="button secondary" href="/dashboard">Cancel</a>
    </div>
  </form>
</div>

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

  @media (max-width: 560px) {
    .form-actions {
      flex-direction: column-reverse;
    }

    .form-actions .button,
    .form-actions button {
      width: 100%;
    }
  }
</style>
