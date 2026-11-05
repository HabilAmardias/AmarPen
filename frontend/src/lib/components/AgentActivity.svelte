<script lang="ts">
  import { CheckCircle, Robot, WarningCircle } from 'phosphor-svelte';
  import type { AgentActivity } from '../api/types';
  import EmptyState from './EmptyState.svelte';
  import StatusBadge from './StatusBadge.svelte';

  export let activity: AgentActivity | null = null;

  $: results = new Map((activity?.results ?? []).map((result) => [result.task_id, result]));
  $: tasks = activity?.tasks ?? [];
</script>

<section class="card stack agent-activity" aria-labelledby="agent-activity-heading">
  <div class="row" style="justify-content: space-between;">
    <span class="panel-kicker">AGENT ACTIVITY</span>
    <Robot size={18} aria-hidden="true" class="text-cyan" />
  </div>
  <div class="row" style="justify-content: space-between;">
    <h2 id="agent-activity-heading">Multi-Agent Tasks</h2>
    <span class="hud-meta"><span>{tasks.length} TASKS</span><span>{activity?.proposals.length ?? 0} PROPOSALS</span></span>
  </div>

  {#if tasks.length === 0}
    <EmptyState title="No agent tasks" message="Agent activity appears when a run starts and the orchestrator proposes work." />
  {:else}
    <div class="table-wrap">
      <table>
        <caption class="sr-only">Agent task activity</caption>
        <thead>
          <tr><th scope="col">Role</th><th scope="col">State</th><th scope="col">Outcome</th><th scope="col">Asset</th><th scope="col">Attempts</th><th scope="col">Limitations</th></tr>
        </thead>
        <tbody>
          {#each tasks as task (task.id)}
            {@const result = results.get(task.id)}
            <tr>
              <td><span class="role-name"><Robot size={13} aria-hidden="true" /> {task.role || task.kind}</span></td>
              <td><StatusBadge value={task.state} /></td>
              <td>
                {#if task.outcome}
                  <StatusBadge value={task.outcome} label={task.outcome} />
                {:else}
                  <span class="muted">Pending</span>
                {/if}
              </td>
              <td class="asset-cell">{task.asset || '—'}</td>
              <td>{task.attempt}/{task.kind === 'orchestrate' ? '∞' : '3'}</td>
              <td class="limits">
                {#if result?.limitations?.length}
                  {#each result.limitations as limitation}
                    <span class="limit-line"><WarningCircle size={12} aria-hidden="true" /> {limitation}</span>
                  {/each}
                {:else}
                  <span class="muted"><CheckCircle size={12} aria-hidden="true" /> None recorded</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    {#if activity?.assets.length}
      <div class="stack">
        <span class="hud-divider">SHARED ASSET MAP</span>
        <ul class="chip-list">
          {#each activity.assets as asset (asset.id)}
            <li class="chip">{asset.kind}: {asset.value}</li>
          {/each}
        </ul>
      </div>
    {/if}
  {/if}
</section>

<style>
  .table-wrap {
    overflow-x: auto;
  }

  .role-name {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--primary);
    white-space: nowrap;
  }

  .asset-cell {
    color: var(--cyan);
    font-size: 0.74rem;
  }

  .limits {
    min-width: 12rem;
  }

  .limit-line {
    display: flex;
    align-items: flex-start;
    gap: 0.3rem;
    color: var(--amber);
    font-size: 0.68rem;
    line-height: 1.35;
  }
</style>
