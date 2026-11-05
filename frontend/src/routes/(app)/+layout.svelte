<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import AppShell from '../../lib/components/AppShell.svelte';
  import LoadingState from '../../lib/components/LoadingState.svelte';
  import { loadSession, session } from '../../lib/stores/session';

  let ready = false;

  onMount(async () => {
    const value = await loadSession();
    if (!value) {
      await goto('/login');
      return;
    }
    ready = true;
  });
</script>

{#if ready}
  <AppShell user={$session?.user ?? null}>
    <slot />
  </AppShell>
{:else}
  <div class="page"><LoadingState label="Checking your session" /></div>
{/if}
