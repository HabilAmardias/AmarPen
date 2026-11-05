<script lang="ts">
  export let label = 'Loading';
</script>

<div class="loading" role="status" aria-live="polite">
  <span class="scan-track" aria-hidden="true"><span class="scan-bar"></span></span>
  <span class="loading-copy">
    <span class="loading-label">{label}</span>
    <span class="loading-dots" aria-hidden="true">...</span>
  </span>
</div>

<style>
  .loading {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 1rem 0;
    color: var(--text-muted);
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .scan-track {
    position: relative;
    width: 2.6rem;
    height: 0.55rem;
    border: 1px solid var(--border);
    overflow: hidden;
    background: var(--surface-inset);
  }

  .scan-bar {
    position: absolute;
    inset: 0;
    width: 45%;
    background: linear-gradient(90deg, transparent, var(--primary), transparent);
    animation: scan 1.4s ease-in-out infinite;
  }

  .loading-copy {
    display: inline-flex;
    align-items: baseline;
    gap: 0.1rem;
  }

  .loading-dots {
    color: var(--primary);
    animation: blink 1.1s steps(2, start) infinite;
  }

  @keyframes scan {
    from {
      transform: translateX(-120%);
    }
    to {
      transform: translateX(240%);
    }
  }
</style>
