<script lang="ts">
  import { WarningOctagon } from 'phosphor-svelte';

  export let open = false;
  export let title = 'Confirm action';
  export let message = '';
  export let confirmLabel = 'Confirm';
  export let danger = false;
  export let onconfirm: () => void = () => {};
  export let oncancel: () => void = () => {};

  function focusConfirm(node: HTMLButtonElement) {
    node.focus();
  }

  function portal(node: HTMLElement) {
    if (typeof document === 'undefined') return;
    document.body.appendChild(node);
    return {
      destroy() {
        node.remove();
      }
    };
  }

  function handleKey(event: KeyboardEvent) {
    if (open && event.key === 'Escape') {
      event.preventDefault();
      oncancel();
    }
  }
</script>

<svelte:window on:keydown={handleKey} />

{#if open}
  <div class="overlay" role="presentation" use:portal>
    <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title" aria-describedby="dialog-message">
      <div class="dialog-kicker">
        <WarningOctagon size={16} weight="bold" aria-hidden="true" />
        <span>{danger ? 'IRREVERSIBLE COMMAND' : 'CONFIRM COMMAND'}</span>
      </div>
      <h2 id="dialog-title">{title}</h2>
      <p id="dialog-message">{message}</p>
      <div class="row dialog-actions">
        <button use:focusConfirm class={danger ? 'danger' : ''} type="button" on:click={onconfirm}>{confirmLabel}</button>
        <button class="secondary" type="button" on:click={oncancel}>Cancel</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(2, 5, 7, 0.78);
    backdrop-filter: blur(5px);
    display: grid;
    place-items: center;
    padding: 1rem;
    z-index: 100;
  }

  .dialog {
    position: relative;
    width: min(100%, 500px);
    padding: 1.35rem;
    border: 1px solid rgba(255, 77, 94, 0.45);
    background:
      linear-gradient(180deg, rgba(24, 12, 15, 0.98), rgba(7, 9, 11, 0.99));
    box-shadow:
      0 0 50px rgba(255, 77, 94, 0.12),
      var(--shadow);
    clip-path: polygon(
      0 10px,
      10px 0,
      100% 0,
      100% calc(100% - 10px),
      calc(100% - 10px) 100%,
      0 100%
    );
  }

  .dialog::before,
  .dialog::after {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    border-color: var(--danger);
    opacity: 0.8;
  }

  .dialog::before {
    top: 0;
    left: 0;
    border-top: 1px solid;
    border-left: 1px solid;
  }

  .dialog::after {
    right: 0;
    bottom: 0;
    border-right: 1px solid;
    border-bottom: 1px solid;
  }

  .dialog-kicker {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--danger);
    font-size: 0.58rem;
    letter-spacing: 0.16em;
    margin-bottom: 0.5rem;
  }

  .dialog h2 {
    color: #ffd7da;
  }

  .dialog p {
    color: var(--text-muted);
    margin: 0 0 1rem;
  }

  .dialog-actions {
    gap: 0.55rem;
  }
</style>
