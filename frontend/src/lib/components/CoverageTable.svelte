<script lang="ts">
  import type { CoverageRecord } from '../api/types';
  import EmptyState from './EmptyState.svelte';
  import StatusBadge from './StatusBadge.svelte';

  export let records: CoverageRecord[] = [];
</script>

{#if records.length === 0}
  <EmptyState title="No coverage records" message="Coverage appears when a run executes approved scenarios." />
{:else}
  <div class="coverage-wrap">
    <table>
      <caption class="sr-only">Coverage by scenario and target</caption>
      <thead>
        <tr>
          <th scope="col">Target</th>
          <th scope="col">Scenario</th>
          <th scope="col">Outcome</th>
          <th scope="col">Reason</th>
        </tr>
      </thead>
      <tbody>
        {#each records as record (record.id)}
          <tr>
            <td class="target-cell">{record.target}</td>
            <td class="scenario-cell">{record.scenario}</td>
            <td><StatusBadge value={record.status} /></td>
            <td class="muted">{record.reason || '—'}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

<style>
  .coverage-wrap {
    overflow-x: auto;
  }

  .target-cell {
    color: var(--cyan);
  }

  .scenario-cell {
    font-size: 0.78rem;
  }
</style>
