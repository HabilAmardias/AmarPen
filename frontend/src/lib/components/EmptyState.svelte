<script lang="ts">
  export let title = 'Nothing here yet';
  export let message = '';
</script>

<div class="empty" role="status">
  <div class="empty-mark" aria-hidden="true">[ ]</div>
  <div class="empty-copy">
    <span class="empty-kicker">NO SIGNAL</span>
    <strong>{title}</strong>
    {#if message}<p class="muted">{message}</p>{/if}
  </div>
  <slot />
</div>

<style>
  .empty {
    display: grid;
    justify-items: center;
    gap: 0.65rem;
    padding: 2rem 1.25rem;
    text-align: center;
    border: 1px dashed var(--border-strong);
    background:
      linear-gradient(rgba(57, 255, 136, 0.025), rgba(57, 255, 136, 0.025)),
      repeating-linear-gradient(
        0deg,
        transparent 0,
        transparent 22px,
        rgba(57, 255, 136, 0.035) 23px
      );
  }

  .empty-mark {
    color: var(--primary);
    font-family: var(--font-display);
    font-size: 1.4rem;
    letter-spacing: 0.18em;
    opacity: 0.7;
  }

  .empty-copy {
    display: grid;
    gap: 0.35rem;
    justify-items: center;
  }

  .empty-copy strong {
    font-family: var(--font-display);
    font-size: 1.05rem;
    font-weight: 400;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .empty-copy p {
    margin: 0;
    max-width: 46ch;
    font-size: 0.84rem;
  }

  .empty-kicker {
    color: var(--text-dim);
    font-size: 0.6rem;
    letter-spacing: 0.16em;
  }
</style>
