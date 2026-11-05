<script lang="ts">
  import { goto } from '$app/navigation';
  import { Fingerprint, Key, ShieldCheck } from 'phosphor-svelte';
  import { api, ApiError } from '../../../lib/api/client';
  import { applyOtpInput, OTP_PATTERN } from '../../../lib/otp';

  let code = '';
  let error = '';
  let pending = false;

  function handleCodeInput(event: Event) {
    code = applyOtpInput(event);
  }

  async function submit() {
    error = '';
    pending = true;
    try {
      const result = await api.auth.totp(code);
      await goto(result.requires_enrollment ? '/account/enroll' : '/dashboard');
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'One-time code verification failed';
    } finally {
      pending = false;
    }
  }
</script>

<svelte:head><title>One-time code | AI-Assisted Pentest</title></svelte:head>

<div class="auth-shell">
  <div class="auth-frame">
    <section class="auth-brief">
      <span class="panel-kicker">SECOND FACTOR REQUIRED</span>
      <h1>Verify Identity<span class="cursor" aria-hidden="true"></span></h1>
      <p class="muted">
        The intermediate password challenge grants access only to MFA completion. A replayed TOTP step is rejected.
      </p>
      <div class="boot-log" aria-label="MFA controls">
        <span>6-DIGIT TOTP / 30 SECOND STEP</span>
        <span>ADJACENT-STEP TOLERANCE: 1</span>
        <span>REPLAY PREVENTION ACTIVE</span>
        <span>GENERIC FAILURE RESPONSES</span>
      </div>
      <div class="auth-badges">
        <span class="badge warning">CHALLENGE OPEN</span>
        <span class="badge">SHORT-LIVED</span>
      </div>
    </section>

    <section class="auth-panel">
      <div class="auth-step"><strong>STEP 02</strong><span>/ 02 · ONE-TIME CODE</span></div>
      <div class="auth-step-rule" aria-hidden="true"></div>
      <div class="auth-icon" aria-hidden="true"><Key size={28} weight="regular" /></div>
      <h2>One-Time Code</h2>
      <p class="muted small">Enter the current code from your enrolled authenticator.</p>

      {#if error}<div class="alert error" role="alert">{error}</div>{/if}

      <form class="stack auth-form" on:submit|preventDefault={submit}>
        <label>
          Authenticator code
          <span class="input-shell otp-shell">
            <Fingerprint size={15} aria-hidden="true" />
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
              aria-describedby="totp-code-hint"
              required
            />
          </span>
        </label>
        <span id="totp-code-hint" class="small muted code-hint">Enter the six-digit code. Spaces and separators are ignored.</span>
        <button type="submit" disabled={pending}>
          <ShieldCheck size={15} weight="bold" aria-hidden="true" />
          {pending ? 'Verifying…' : 'Verify and sign in'}
        </button>
      </form>

      <a class="small auth-help" href="/login">← Back to password step</a>
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

  .auth-help {
    display: inline-block;
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

  .otp-shell input {
    font-family: var(--font-display);
    font-size: 1.35rem;
    letter-spacing: 0.5em;
    text-align: center;
  }

  .input-shell input:focus {
    box-shadow: none;
  }
</style>
