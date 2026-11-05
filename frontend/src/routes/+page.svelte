<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { ShieldCheck, Terminal } from 'phosphor-svelte';
  import LoadingState from '../lib/components/LoadingState.svelte';
  import { loadSession } from '../lib/stores/session';

  let error = '';

  onMount(async () => {
    try {
      const value = await loadSession();
      await goto(value ? '/dashboard' : '/login');
    } catch {
      error = 'Unable to start the application.';
    }
  });
</script>

<svelte:head><title>Boot | AI-Assisted Pentest</title></svelte:head>

<div class="auth-shell">
  <div class="boot-panel">
    <span class="panel-kicker">SYSTEM BOOT</span>
    <div class="boot-mark" aria-hidden="true">
      <Terminal size={34} weight="regular" />
    </div>
    <h1>Initializing Console<span class="cursor" aria-hidden="true"></span></h1>
    {#if error}
      <div class="alert error" role="alert">{error}</div>
    {:else}
      <LoadingState label="Resolving local session" />
      <div class="boot-log">
        <span>VERIFYING SESSION MATERIAL</span>
        <span>LOADING OPERATOR CONTEXT</span>
        <span>ROUTING TO COMMAND DECK</span>
      </div>
    {/if}
    <div class="boot-footer">
      <ShieldCheck size={14} aria-hidden="true" /> LOCAL NODE / ENCRYPTED CHANNEL
    </div>
  </div>
</div>

<style>
  .boot-panel {
    width: min(100%, 480px);
    display: grid;
    justify-items: center;
    gap: 0.75rem;
    padding: 2rem 1.5rem;
    text-align: center;
    border: 1px solid var(--border);
    background:
      radial-gradient(circle at 50% 0%, rgba(57, 255, 136, 0.08), transparent 60%),
      linear-gradient(180deg, rgba(15, 26, 32, 0.96), rgba(5, 8, 10, 0.98));
    clip-path: polygon(0 12px, 12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%);
  }

  .boot-mark {
    color: var(--primary);
    margin-top: 0.4rem;
    filter: drop-shadow(0 0 16px rgba(57, 255, 136, 0.25));
  }

  .boot-log {
    justify-self: stretch;
    margin-top: 0.4rem;
    text-align: left;
  }

  .boot-footer {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.6rem;
    color: var(--text-dim);
    font-size: 0.58rem;
    letter-spacing: 0.12em;
  }
</style>
