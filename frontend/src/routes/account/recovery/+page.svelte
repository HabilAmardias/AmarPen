<script lang="ts">
  import { goto } from '$app/navigation';
  import { ArrowLeft, Key, Lifebuoy, ShieldCheck } from 'phosphor-svelte';
  import { api, ApiError } from '../../../lib/api/client';

  let username = '';
  let recoveryCode = '';
  let newPassword = '';
  let error = '';
  let success = false;
  let pending = false;

  async function submit() {
    error = '';
    pending = true;
    try {
      await api.auth.recovery(username, recoveryCode, newPassword);
      success = true;
      setTimeout(() => goto('/login'), 800);
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Recovery failed';
    } finally {
      pending = false;
    }
  }
</script>

<svelte:head><title>Account recovery | AI-Assisted Pentest</title></svelte:head>

<div class="auth-shell">
  <div class="auth-frame">
    <section class="auth-brief">
      <span class="panel-kicker">ACCOUNT RECOVERY</span>
      <h1>Restore Access<span class="cursor" aria-hidden="true"></span></h1>
      <p class="muted">
        A consumed recovery code cannot be reused. Recovery does not create a password-only session; the enrolled factor remains required.
      </p>
      <div class="boot-log" aria-label="Recovery controls">
        <span>SINGLE-USE CODE CONSUMPTION</span>
        <span>SESSIONS REVOKED ON RESET</span>
        <span>GENERIC FAILURE RESPONSES</span>
        <span>ATTRIBUTED RECOVERY ACTION</span>
      </div>
      <div class="auth-badges">
        <span class="badge warning">RECOVERY PATH</span>
        <span class="badge">NO SECRET EXPOSURE</span>
      </div>
    </section>

    <section class="auth-panel">
      <div class="auth-step"><strong>RECOVERY</strong><span>/ LOCAL ACCOUNT</span></div>
      <div class="auth-step-rule" aria-hidden="true"></div>
      <div class="auth-icon" aria-hidden="true"><Lifebuoy size={28} weight="regular" /></div>

      {#if error}<div class="alert error" role="alert">{error}</div>{/if}

      {#if success}
        <div class="alert success" role="status">
          <ShieldCheck size={15} aria-hidden="true" /> Recovery completed. Redirecting to sign in.
        </div>
      {:else}
        <h2>Recovery Console</h2>
        <form class="stack auth-form" on:submit|preventDefault={submit}>
          <label>Username <input name="username" bind:value={username} required /></label>
          <label>
            Recovery code
            <span class="input-shell">
              <Key size={15} aria-hidden="true" />
              <input name="recovery_code" bind:value={recoveryCode} required />
            </span>
          </label>
          <label>
            New password
            <input name="new_password" type="password" minlength="12" bind:value={newPassword} required />
          </label>
          <button type="submit" disabled={pending}>
            <ShieldCheck size={15} weight="bold" aria-hidden="true" />
            {pending ? 'Recovering…' : 'Recover account'}
          </button>
        </form>
      {/if}

      <a class="small auth-help" href="/login"><ArrowLeft size={13} aria-hidden="true" /> Back to sign in</a>
    </section>
  </div>
</div>

<style>
  .auth-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 1.2rem;
  }

  .auth-step-rule {
    height: 1px;
    margin: 0.6rem 0 1rem;
    background: linear-gradient(90deg, var(--primary), transparent);
    opacity: 0.35;
  }

  .auth-icon {
    color: var(--primary);
    margin-bottom: 0.6rem;
    filter: drop-shadow(0 0 10px rgba(57, 255, 136, 0.25));
  }

  .auth-form {
    margin-top: 1rem;
  }

  .auth-help {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    margin-top: 1rem;
    text-decoration: none;
  }

  .input-shell {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding-left: 0.65rem;
    border: 1px solid var(--border);
    background: var(--surface-inset);
    color: var(--text-dim);
  }

  .input-shell:focus-within {
    border-color: var(--primary);
    box-shadow: 0 0 18px rgba(57, 255, 136, 0.08);
    color: var(--primary);
  }

  .input-shell input {
    border: 0;
    background: transparent;
    box-shadow: none;
    padding-left: 0;
  }
</style>
