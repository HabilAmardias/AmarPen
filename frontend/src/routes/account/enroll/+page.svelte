<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { CheckCircle, Copy, Key, ShieldCheck } from 'phosphor-svelte';
  import { api, ApiError } from '../../../lib/api/client';
  import LoadingState from '../../../lib/components/LoadingState.svelte';
  import { applyOtpInput, OTP_PATTERN } from '../../../lib/otp';

  let secret = '';
  let provisioningUri = '';
  let code = '';
  let recoveryCodes: string[] = [];
  let error = '';
  let pending = false;

  onMount(async () => {
    try {
      const result = await api.auth.enrollmentStart();
      secret = result.secret;
      provisioningUri = result.provisioning_uri;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to start enrollment';
    }
  });

  async function verify() {
    error = '';
    pending = true;
    try {
      const result = await api.auth.enrollmentVerify(code);
      recoveryCodes = result.recovery_codes;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Enrollment verification failed';
    } finally {
      pending = false;
    }
  }

  function handleCodeInput(event: Event) {
    code = applyOtpInput(event);
  }

  async function copySecret() {
    try {
      await navigator.clipboard.writeText(secret);
    } catch {
      return;
    }
  }
</script>

<svelte:head><title>Enroll authenticator | AI-Assisted Pentest</title></svelte:head>

<div class="auth-shell">
  <div class="auth-frame">
    <section class="auth-brief">
      <span class="panel-kicker">MFA ENROLLMENT</span>
      <h1>Bind Authenticator<span class="cursor" aria-hidden="true"></span></h1>
      <p class="muted">
        Verify the authenticator before activation. Recovery codes are single-use and shown only once.
      </p>
      <div class="boot-log" aria-label="Enrollment controls">
        <span>TOTP SECRET ENCRYPTED AT REST</span>
        <span>UNVERIFIED FACTOR REMAINS INACTIVE</span>
        <span>RECOVERY CODES STORED AS HASHES</span>
        <span>FACTOR RESET REVOKES SESSIONS</span>
      </div>
      <div class="auth-badges">
        <span class="badge warning">ENROLLMENT OPEN</span>
        <span class="badge">ADMINISTRATOR VISIBLE</span>
      </div>
    </section>

    <section class="auth-panel">
      <div class="auth-step"><strong>MFA</strong><span>/ FACTOR BINDING</span></div>
      <div class="auth-step-rule" aria-hidden="true"></div>
      <div class="auth-icon" aria-hidden="true"><Key size={28} weight="regular" /></div>

      {#if error}<div class="alert error" role="alert">{error}</div>{/if}

      {#if recoveryCodes.length}
        <div class="alert success" role="status">
          <strong>Enrollment complete.</strong> Store these single-use recovery codes securely. They will not be shown again.
        </div>
        <ul class="code-grid">
          {#each recoveryCodes as recoveryCode}
            <li><code>{recoveryCode}</code></li>
          {/each}
        </ul>
        <button type="button" class="enroll-continue" on:click={() => goto('/dashboard')}>
          <CheckCircle size={15} weight="bold" aria-hidden="true" />
          Continue to dashboard
        </button>
      {:else if provisioningUri}
        <h2>Authenticator Binding</h2>
        <p class="muted small">Add this account to your authenticator, then enter the current six-digit code.</p>
        <div class="secret-panel">
          <div>
            <span class="small muted">Manual secret</span>
            <code>{secret}</code>
          </div>
          <button type="button" class="secondary copy-button" on:click={copySecret}>
            <Copy size={14} aria-hidden="true" /> Copy
          </button>
          <a href={provisioningUri}>Open provisioning URI</a>
        </div>
        <form class="stack auth-form" on:submit|preventDefault={verify}>
          <label>
            Verification code
            <span class="input-shell">
              <Key size={15} aria-hidden="true" />
              <input
                name="code"
                type="text"
                inputmode="numeric"
                autocomplete="one-time-code"
                autocapitalize="off"
                spellcheck="false"
                enterkeyhint="done"
                pattern={OTP_PATTERN}
                value={code}
                on:input={handleCodeInput}
                aria-describedby="enroll-code-hint"
                required
              />
            </span>
          </label>
          <span id="enroll-code-hint" class="small muted code-hint">Enter the six-digit code. Spaces and separators are ignored.</span>
          <button type="submit" disabled={pending}>
            <ShieldCheck size={15} weight="bold" aria-hidden="true" />
            {pending ? 'Verifying…' : 'Verify enrollment'}
          </button>
        </form>
      {:else}
        <LoadingState label="Preparing enrollment" />
      {/if}
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

  .code-hint {
    margin-top: -0.2rem;
  }

  .secret-panel {
    display: grid;
    gap: 0.55rem;
    padding: 0.75rem;
    border: 1px solid var(--border);
    background: var(--surface-inset);
    margin-bottom: 1rem;
  }

  .secret-panel > div {
    display: grid;
    gap: 0.2rem;
  }

  .secret-panel code {
    font-size: 1rem;
    letter-spacing: 0.18em;
    padding: 0.25rem 0.35rem;
  }

  .copy-button {
    justify-self: start;
  }

  .code-grid {
    margin: 1rem 0;
  }

  .enroll-continue {
    margin-top: 1rem;
    width: 100%;
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
