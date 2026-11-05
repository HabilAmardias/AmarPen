<script lang="ts">
  import { WarningOctagon } from 'phosphor-svelte';

  export let title = 'Something went wrong';
  export let message = 'The request could not be completed.';
  export let correlationId = '';
  export let onretry: (() => void) | null = null;
</script>

<div class="alert error fault" role="alert">
  <div class="fault-head">
    <WarningOctagon size={20} weight="bold" aria-hidden="true" />
    <div>
      <span class="fault-kicker">FAULT DETECTED</span>
      <strong>{title}</strong>
    </div>
  </div>
  <p>{message}</p>
  {#if correlationId}
    <p class="correlation"><span>CORRELATION</span> <code>{correlationId}</code></p>
  {/if}
  {#if onretry}
    <button class="secondary" type="button" on:click={onretry}>Try again</button>
  {/if}
</div>

<style>
  .fault {
    display: grid;
    gap: 0.65rem;
    padding: 1rem;
  }

  .fault-head {
    display: flex;
    align-items: flex-start;
    gap: 0.55rem;
  }

  .fault-head strong {
    display: block;
    font-family: var(--font-display);
    font-size: 1.05rem;
    font-weight: 400;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }

  .fault-kicker {
    display: block;
    margin-bottom: 0.12rem;
    color: var(--danger);
    font-size: 0.58rem;
    letter-spacing: 0.16em;
  }

  .fault p {
    margin: 0;
  }

  .correlation {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    flex-wrap: wrap;
    font-size: 0.72rem;
    color: var(--text-muted);
  }

  .correlation span {
    color: var(--text-dim);
    font-size: 0.58rem;
    letter-spacing: 0.12em;
  }

  .fault button {
    justify-self: start;
  }
</style>
