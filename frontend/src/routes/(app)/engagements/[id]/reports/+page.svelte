<script lang="ts">
  import { onMount } from 'svelte';
  import { ArrowLeft, CheckCircle, Download, Eye, FilePdf, Stamp } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../../lib/api/client';
  import type { ReportSnapshot } from '../../../../../lib/api/types';
  import EmptyState from '../../../../../lib/components/EmptyState.svelte';
  import LoadingState from '../../../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../../../lib/components/StatusBadge.svelte';

  export let data: { id: string };

  let reports: ReportSnapshot[] = [];
  let partial = false;
  let loading = true;
  let error = '';
  let notice = '';

  async function load() {
    loading = true;
    error = '';
    try {
      reports = (await api.reports.list(data.id)).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load reports';
    } finally {
      loading = false;
    }
  }

  async function action(work: () => Promise<unknown>, message: string) {
    error = '';
    notice = '';
    try {
      await work();
      await load();
      notice = message;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Report operation failed';
    }
  }

  onMount(load);
</script>

<svelte:head><title>Reports | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="operation-header">
    <div>
      <span class="panel-kicker">REPORT ARCHIVE</span>
      <h1>Report Snapshots</h1>
      <p class="muted">A final PDF is generated only from an approved immutable snapshot.</p>
    </div>
    <a class="button secondary" href={`/engagements/${data.id}`}><ArrowLeft size={14} aria-hidden="true" /> Overview</a>
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}
  {#if notice}<div class="alert success" role="status">{notice}</div>{/if}

  <div class="card row snapshot-bar">
    <label class="checkbox"><input type="checkbox" bind:checked={partial} /> Partial assessment</label>
    <span class="small muted">Preview before approval. Approved snapshots are immutable.</span>
    <button
      type="button"
      on:click={() => action(() => api.reports.create(data.id, partial), 'Report snapshot created.')}
    >
      <FilePdf size={14} weight="bold" aria-hidden="true" /> Create snapshot
    </button>
  </div>

  {#if loading}
    <LoadingState label="Loading reports" />
  {:else if reports.length === 0}
    <EmptyState title="No report snapshots" message="Create a snapshot after findings are validated and reviewed." />
  {:else}
    <div class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 0.5rem;">
        <span class="panel-kicker">IMMUTABLE VERSIONS</span>
        <span class="hud-meta"><span>{reports.length} SNAPSHOTS</span></span>
      </div>
      <table>
        <caption class="sr-only">Report versions</caption>
        <thead><tr><th scope="col">Version</th><th scope="col">Status</th><th scope="col">Created</th><th scope="col">Actions</th></tr></thead>
        <tbody>
          {#each reports as report (report.id)}
            <tr>
              <td><span class="version-tag">v{report.version}</span></td>
              <td><StatusBadge value={report.status} /></td>
              <td class="muted">{new Date(report.created_at).toLocaleString()}</td>
              <td>
                <div class="row action-row">
                  <button type="button" class="secondary" on:click={() => action(() => api.reports.approve(report.id), 'Report approved.')}>
                    <Stamp size={13} aria-hidden="true" /> Approve
                  </button>
                  <button type="button" class="secondary" on:click={() => action(() => api.reports.render(report.id), 'PDF rendered from snapshot.')}>
                    <CheckCircle size={13} aria-hidden="true" /> Render
                  </button>
                  <a class="button secondary" href={api.reports.previewUrl(report.id)} target="_blank" rel="noreferrer">
                    <Eye size={13} aria-hidden="true" /> Preview
                  </a>
                  <a class="button secondary" href={api.reports.downloadUrl(report.id)}>
                    <Download size={13} aria-hidden="true" /> Download
                  </a>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .snapshot-bar {
    align-items: center;
  }

  .snapshot-bar .checkbox {
    width: auto;
  }

  .snapshot-bar button {
    margin-left: auto;
  }

  .version-tag {
    display: inline-flex;
    padding: 0.12rem 0.38rem;
    border: 1px solid rgba(57, 255, 136, 0.3);
    color: var(--primary);
    font-family: var(--font-display);
    font-size: 0.78rem;
  }

  .action-row {
    gap: 0.35rem;
  }

  .action-row button,
  .action-row .button {
    min-height: 2rem;
    padding: 0.34rem 0.55rem;
    font-size: 0.62rem;
  }

  @media (max-width: 560px) {
    .snapshot-bar button {
      margin-left: 0;
      width: 100%;
    }
  }
</style>
