<script lang="ts">
  import { goto } from '$app/navigation';
  import { Fingerprint, LockKey, ShieldCheck, Terminal } from 'phosphor-svelte';
  import { api, ApiError } from '../../lib/api/client';

  let username = '';
  let password = '';
  let error = '';
  let pending = false;

  async function submit() {
    error = '';
    pending = true;
    try {
      const result = await api.auth.login(username, password);
      if (result.next === 'enrollment') {
        await goto('/account/enroll');
      } else if (result.next === 'totp') {
        await goto('/login/totp');
      } else {
        await goto('/dashboard');
      }
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Sign in failed';
    } finally {
      pending = false;
    }
  }
</script>

<svelte:head><title>Sign in | AI-Assisted Pentest</title></svelte:head>

<div class="auth-shell">
  <div class="auth-frame">
    <section class="auth-brief">
      <span class="panel-kicker">AIPENTEST//OPS</span>
      <h1>Secure Access<span class="cursor" aria-hidden="true"></span></h1>
      <p class="muted">
        Local operator authentication. Password verification is followed by a mandatory one-time code.
      </p>
      <div class="boot-log" aria-label="Security baseline">
        <span>LOCAL IDENTITY STORE</span>
        <span>ARGON2ID / TOTP MFA</span>
        <span>HTTP-ONLY SERVER SESSIONS</span>
        <span>CSRF PROTECTED MUTATIONS</span>
      </div>
      <div class="auth-badges">
        <span class="badge success">ON-PREMISES</span>
        <span class="badge">NO CLOUD IDENTITY</span>
      </div>
    </section>

    <section class="auth-panel">
      <div class="auth-step"><strong>STEP 01</strong><span>/ 02 · PASSWORD</span></div>
      <div class="auth-step-rule" aria-hidden="true"></div>
      <div class="auth-icon" aria-hidden="true"><Terminal size={28} weight="regular" /></div>
      <h2>Operator Sign In</h2>
      <p class="muted small">Use your local account. Protected resources remain inaccessible until MFA completes.</p>

      {#if error}<div class="alert error" role="alert">{error}</div>{/if}

      <form class="stack auth-form" on:submit|preventDefault={submit}>
        <label>
          Username
          <span class="input-shell">
            <Fingerprint size={15} aria-hidden="true" />
            <input name="username" autocomplete="username" bind:value={username} required />
          </span>
        </label>
        <label>
          Password
          <span class="input-shell">
            <LockKey size={15} aria-hidden="true" />
            <input name="password" type="password" autocomplete="current-password" bind:value={password} required />
          </span>
        </label>
        <button type="submit" disabled={pending}>
          <ShieldCheck size={15} weight="bold" aria-hidden="true" />
          {pending ? 'Signing in…' : 'Continue'}
        </button>
      </form>

      <p class="small muted auth-help">
        Lost your authenticator? <a href="/account/recovery">Use a recovery code</a>.
      </p>
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

  .input-shell {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding-left: 0.65rem;
    border: 1px solid var(--border);
    background: var(--surface-inset);
    color: var(--text-dim);
    transition:
      border-color 160ms ease,
      box-shadow 160ms ease;
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

  .input-shell input:focus {
    box-shadow: none;
  }

  .auth-help {
    margin: 1rem 0 0;
  }
</style>
