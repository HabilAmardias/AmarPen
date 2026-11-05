<script lang="ts">
  import { ArrowLeft, WarningOctagon } from 'phosphor-svelte';
  import ErrorView from '../lib/components/ErrorView.svelte';
</script>

<svelte:head><title>Signal lost | AI-Assisted Pentest</title></svelte:head>

<div class="auth-shell">
  <div class="error-frame">
    <span class="panel-kicker">ROUTE FAILURE</span>
    <div class="error-code" aria-hidden="true">ERR / 404</div>
    <div class="error-icon" aria-hidden="true"><WarningOctagon size={40} weight="regular" /></div>
    <h1>Page unavailable</h1>
    <ErrorView
      title="This page could not be loaded"
      message="The route may be unavailable or your session may have expired."
    />
    <a class="button" href="/dashboard"><ArrowLeft size={14} aria-hidden="true" /> Return to dashboard</a>
  </div>
</div>

<style>
  .error-frame {
    width: min(100%, 560px);
    display: grid;
    justify-items: start;
    gap: 0.75rem;
    padding: 2rem;
    border: 1px solid rgba(255, 77, 94, 0.35);
    background:
      radial-gradient(circle at 20% 0%, rgba(255, 77, 94, 0.08), transparent 60%),
      linear-gradient(180deg, rgba(24, 12, 15, 0.96), rgba(5, 8, 10, 0.98));
    clip-path: polygon(0 12px, 12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%);
  }

  .error-code {
    color: var(--danger);
    font-size: 0.62rem;
    letter-spacing: 0.2em;
  }

  .error-icon {
    color: var(--danger);
    filter: drop-shadow(0 0 18px rgba(255, 77, 94, 0.22));
  }

  .error-frame h1 {
    color: #ffd7da;
  }

  .error-frame :global(.fault) {
    width: 100%;
  }
</style>
