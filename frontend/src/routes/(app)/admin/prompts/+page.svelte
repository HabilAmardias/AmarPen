<script lang="ts">
  import { onMount } from 'svelte';
  import { CheckCircle, FileCode, GitBranch, Rocket, ShieldCheck } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';
  import type { PromptRelease, SystemPrompt } from '../../../../lib/api/types';
  import ErrorView from '../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../../lib/components/StatusBadge.svelte';

  let prompts: SystemPrompt[] = [];
  let releases: PromptRelease[] = [];
  let loading = true;
  let error = '';
  let notice = '';

  let key = 'agent-orchestrator';
  let agentRole = 'orchestrator';
  let purpose = '';
  let body = '';
  let changeReason = '';
  let releaseName = 'baseline-2';
  let manifest = '{\n  "orchestrator": "prompt-1"\n}';

  async function load() {
    loading = true;
    error = '';
    try {
      prompts = (await api.prompts.list(true)).items;
      releases = (await api.prompts.releases()).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load system prompts';
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
      error = cause instanceof ApiError ? cause.message : 'System prompt operation failed';
    }
  }

  async function createDraft() {
    await action(
      () => api.prompts.create({ key, agent_role: agentRole, purpose, body, change_reason: changeReason }),
      'Draft created.'
    );
  }

  async function createRelease() {
    await action(async () => {
      const parsed = JSON.parse(manifest) as Record<string, string>;
      return api.prompts.createRelease(releaseName, parsed);
    }, 'Release draft created.');
  }

  onMount(load);
</script>

<svelte:head><title>System prompts | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="alert">
    <ShieldCheck size={16} aria-hidden="true" />
    Administrator-only system instruction library. Published versions are immutable; active runs retain their pinned release.
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}
  {#if notice}<div class="alert success" role="status">{notice}</div>{/if}

  <div class="grid two">
    <form class="card stack" on:submit|preventDefault={createDraft}>
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">CREATE DRAFT</span>
        <FileCode size={17} aria-hidden="true" class="text-green" />
      </div>
      <div class="grid two">
        <label>Stable key <input bind:value={key} required /></label>
        <label>Agent role <input bind:value={agentRole} required /></label>
      </div>
      <label>Purpose <input bind:value={purpose} /></label>
      <label>System instructions <textarea class="code-editor" bind:value={body} required></textarea></label>
      <label>Change reason <input bind:value={changeReason} required /></label>
      <button type="submit"><FileCode size={14} weight="bold" aria-hidden="true" /> Save draft</button>
    </form>

    <form class="card stack" on:submit|preventDefault={createRelease}>
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">CREATE RELEASE</span>
        <GitBranch size={17} aria-hidden="true" class="text-cyan" />
      </div>
      <label>Release name <input bind:value={releaseName} required /></label>
      <label>Agent and prompt manifest (JSON) <textarea class="code-editor" bind:value={manifest}></textarea></label>
      <p class="small muted">Only published prompts can enter a release. Activation is atomic and audited.</p>
      <button type="submit"><Rocket size={14} weight="bold" aria-hidden="true" /> Create release draft</button>
    </form>
  </div>

  {#if loading}
    <LoadingState label="Loading prompts" />
  {:else if error && prompts.length === 0}
    <ErrorView title="Could not load prompts" message={error} onretry={load} />
  {:else}
    <section class="card stack">
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">VERSION LIBRARY</span>
        <span class="hud-meta"><span>{prompts.length} VERSIONS</span></span>
      </div>
      <h2>System Instructions</h2>
      <table>
        <caption class="sr-only">System prompt versions</caption>
        <thead><tr><th scope="col">Key</th><th scope="col">Agent</th><th scope="col">Version</th><th scope="col">State</th><th scope="col">Action</th></tr></thead>
        <tbody>
          {#each prompts as prompt (prompt.id)}
            <tr>
              <td>
                <span class="prompt-key">{prompt.key}</span>
                <div class="small muted prompt-preview">{prompt.body?.slice(0, 90) ?? 'Body hidden'}</div>
              </td>
              <td>{prompt.agent_role}</td>
              <td><span class="version-tag">v{prompt.version}</span></td>
              <td><StatusBadge value={prompt.state} /></td>
              <td>
                <div class="row action-row">
                  <button type="button" class="secondary" on:click={() => action(() => api.prompts.validate(prompt.id), 'Validation recorded.')}>
                    <CheckCircle size={13} aria-hidden="true" /> Validate
                  </button>
                  <button type="button" class="secondary" on:click={() => action(() => api.prompts.publish(prompt.id), 'Prompt published.')}>
                    <Rocket size={13} aria-hidden="true" /> Publish
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>

    <section class="card stack">
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">RELEASE MANIFESTS</span>
        <span class="hud-meta"><span>{releases.length} RELEASES</span></span>
      </div>
      <h2>Releases</h2>
      {#if releases.length === 0}
        <p class="muted">No releases recorded.</p>
      {:else}
        <table>
          <caption class="sr-only">Prompt releases</caption>
          <thead><tr><th scope="col">Name</th><th scope="col">Version</th><th scope="col">State</th><th scope="col">Action</th></tr></thead>
          <tbody>
            {#each releases as release (release.id)}
              <tr>
                <td>{release.name}</td>
                <td><span class="version-tag">v{release.version}</span></td>
                <td><StatusBadge value={release.state} /></td>
                <td>
                  <div class="row action-row">
                    <button type="button" class="secondary" on:click={() => action(() => api.prompts.validateRelease(release.id), 'Release validated.')}>Validate</button>
                    <button type="button" class="secondary" on:click={() => action(() => api.prompts.activateRelease(release.id, 'Administrator activation'), 'Release activated.')}>Activate</button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </section>
  {/if}
</div>

<style>
  .code-editor {
    min-height: 11rem;
    background:
      repeating-linear-gradient(
        0deg,
        rgba(57, 255, 136, 0.025) 0,
        rgba(57, 255, 136, 0.025) 1px,
        transparent 1px,
        transparent 21px
      ),
      var(--surface-inset);
    color: #bfffd8;
    font-size: 0.8rem;
  }

  .prompt-key {
    color: var(--primary);
    font-size: 0.78rem;
  }

  .prompt-preview {
    max-width: 34rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .version-tag {
    display: inline-flex;
    padding: 0.1rem 0.34rem;
    border: 1px solid rgba(57, 255, 136, 0.3);
    color: var(--primary);
    font-family: var(--font-display);
    font-size: 0.72rem;
  }

  .action-row {
    gap: 0.3rem;
  }

  .action-row button {
    min-height: 1.9rem;
    padding: 0.28rem 0.46rem;
    font-size: 0.58rem;
  }
</style>
