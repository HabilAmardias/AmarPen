<script lang="ts">
  import { onMount } from 'svelte';
  import { BookOpen, GitBranch, PencilSimple, Rocket, UploadSimple } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';
  import type { SkillPackSummary, SkillReleaseSummary } from '../../../../lib/api/types';

  let packs: SkillPackSummary[] = [];
  let releases: SkillReleaseSummary[] = [];
  let loading = true;
  let error = '';
  let notice = '';
  let editingId = '';
  let expectedVersion = 1;

  let key = '';
  let name = '';
  let category = 'wstg';
  let source = '';
  let description = '';
  let changeReason = 'Administrator skill pack update';
  let skillsJson = JSON.stringify(
    [
      {
        key: 'example.skill',
        title: 'Example skill',
        category: 'wstg',
        source_refs: ['WSTG-INFO-01'],
        hypothesis: 'Describe the security hypothesis.',
        applicability: { endpoint_types: ['web'], methods: ['GET'] },
        scenario_keys: ['WSTG-INFO-01'],
        prerequisites: [],
        probe_strategy: ['baseline', 'bounded comparison'],
        evidence_criteria: ['baseline evidence', 'comparison evidence'],
        stop_conditions: ['scope mismatch'],
        prompt_fragment: 'Use only approved playbook steps and bounded evidence.'
      }
    ],
    null,
    2
  );
  let releaseName = 'skills-baseline';
  let releaseManifest = '{}';

  async function load() {
    loading = true;
    error = '';
    try {
      packs = (await api.admin.skillPacks(true)).items;
      releases = (await api.admin.skillReleases()).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load skill packs';
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
      error = cause instanceof ApiError ? cause.message : 'Skill operation failed';
    }
  }

  async function savePack() {
    let skills: unknown;
    try {
      skills = JSON.parse(skillsJson);
    } catch {
      error = 'Skills JSON is invalid.';
      return;
    }
    if (editingId) {
      await action(
        () => api.admin.updateSkillPack(editingId, { expected_version: expectedVersion, name, category, source, description, skills, change_reason: changeReason }),
        'Skill draft updated.'
      );
    } else {
      await action(
        () => api.admin.createSkillPack({ key, name, category, source, description, skills, change_reason: changeReason }),
        'Skill pack installed as draft.'
      );
    }
    if (!editingId) {
      key = '';
      name = '';
    }
  }

  function editPack(pack: SkillPackSummary) {
    editingId = pack.id;
    expectedVersion = pack.version;
    key = pack.key;
    name = pack.name;
    category = pack.category;
    source = pack.source;
    description = pack.description;
    changeReason = `Edit ${pack.key} v${pack.version}`;
    skillsJson = JSON.stringify(pack.skills ?? [], null, 2);
  }

  function newPack() {
    editingId = '';
    expectedVersion = 1;
    key = '';
    name = '';
    category = 'wstg';
    source = '';
    description = '';
    changeReason = 'Administrator skill pack update';
  }

  async function createRelease() {
    let manifest: Record<string, string>;
    try {
      manifest = JSON.parse(releaseManifest) as Record<string, string>;
    } catch {
      error = 'Release manifest JSON is invalid.';
      return;
    }
    await action(() => api.admin.createSkillRelease(releaseName, manifest), 'Skill release draft created.');
  }

  function useActiveManifest() {
    const active = releases.find((release) => release.state === 'ACTIVE');
    releaseManifest = JSON.stringify(active?.manifest ?? Object.fromEntries(packs.filter((pack) => pack.state === 'PUBLISHED').map((pack) => [pack.key, pack.id])), null, 2);
  }

  onMount(load);
</script>

<svelte:head><title>Skills | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="alert">
    <BookOpen size={17} aria-hidden="true" />
    <span>Administrator-managed cybersecurity skill packs. Runs pin the active skill release; edits never affect existing runs.</span>
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}
  {#if notice}<div class="alert success" role="status">{notice}</div>{/if}

  <div class="grid two">
    <form class="card stack" on:submit|preventDefault={savePack}>
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">{editingId ? 'EDIT DRAFT PACK' : 'INSTALL SKILL PACK'}</span>
        <UploadSimple size={17} aria-hidden="true" class="text-green" />
      </div>
      <div class="grid two">
        <label>Pack key <input bind:value={key} required disabled={!!editingId} /></label>
        <label>Name <input bind:value={name} required /></label>
        <label>Category <input bind:value={category} required /></label>
        <label>Source <input bind:value={source} /></label>
      </div>
      <label>Description <input bind:value={description} /></label>
      <label>Skills JSON <textarea class="code-editor" bind:value={skillsJson} required></textarea></label>
      <label>Change reason <input bind:value={changeReason} required /></label>
      <div class="row action-row">
        <button type="submit"><BookOpen size={14} weight="bold" aria-hidden="true" /> {editingId ? 'Save draft' : 'Install pack'}</button>
        {#if editingId}<button type="button" class="secondary" on:click={newPack}>Cancel edit</button>{/if}
      </div>
    </form>

    <form class="card stack" on:submit|preventDefault={createRelease}>
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">SKILL RELEASE</span>
        <GitBranch size={17} aria-hidden="true" class="text-cyan" />
      </div>
      <label>Release name <input bind:value={releaseName} required /></label>
      <label>Pack manifest <textarea class="code-editor" bind:value={releaseManifest} required></textarea></label>
      <div class="row action-row">
        <button type="submit"><Rocket size={14} weight="bold" aria-hidden="true" /> Create release draft</button>
        <button type="button" class="secondary" on:click={useActiveManifest}>Use published packs</button>
      </div>
    </form>
  </div>

  {#if loading}
    <p class="muted">Loading skill library…</p>
  {:else}
    <section class="card stack">
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">SKILL PACK VERSIONS</span>
        <span class="hud-meta"><span>{packs.length} PACKS</span></span>
      </div>
      <table>
        <caption class="sr-only">Skill packs</caption>
        <thead><tr><th scope="col">Pack</th><th scope="col">Category</th><th scope="col">Version</th><th scope="col">State</th><th scope="col">Skills</th><th scope="col">Actions</th></tr></thead>
        <tbody>
          {#each packs as pack (pack.id)}
            <tr>
              <td><span class="pack-key">{pack.key}</span><div class="small muted">{pack.name}</div></td>
              <td>{pack.category}</td>
              <td>v{pack.version}</td>
              <td>{pack.state}</td>
              <td>{pack.skill_count}</td>
              <td>
                <div class="row action-row">
                  <button type="button" class="secondary" on:click={() => action(() => api.admin.validateSkillPack(pack.id), 'Skill pack validation recorded.')}>Validate</button>
                  <button type="button" class="secondary" on:click={() => action(() => api.admin.publishSkillPack(pack.id), 'Skill pack published.')}>Publish</button>
                  {#if pack.state === 'DRAFT'}<button type="button" class="secondary" on:click={() => editPack(pack)}><PencilSimple size={12} aria-hidden="true" /> Edit</button>{/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>

    <section class="card stack">
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">RELEASES</span>
        <span class="hud-meta"><span>{releases.length} RELEASES</span></span>
      </div>
      {#if releases.length === 0}
        <p class="muted">No skill releases recorded.</p>
      {:else}
        <table>
          <caption class="sr-only">Skill releases</caption>
          <thead><tr><th scope="col">Name</th><th scope="col">Version</th><th scope="col">State</th><th scope="col">Validated</th><th scope="col">Actions</th></tr></thead>
          <tbody>
            {#each releases as release (release.id)}
              <tr>
                <td>{release.name}</td>
                <td>v{release.version}</td>
                <td>{release.state}</td>
                <td>{release.validated ? 'Yes' : 'No'}</td>
                <td>
                  <div class="row action-row">
                    <button type="button" class="secondary" on:click={() => action(() => api.admin.validateSkillRelease(release.id), 'Skill release validated.')}>Validate</button>
                    <button type="button" class="secondary" on:click={() => action(() => api.admin.activateSkillRelease(release.id, 'Administrator activation'), 'Skill release activated.')}>Activate</button>
                    {#if release.state === 'ACTIVE'}<button type="button" class="secondary" on:click={() => action(() => api.admin.rollbackSkillRelease(release.id, 'Administrator rollback'), 'Skill release rolled back.')}>Rollback</button>{/if}
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
    min-height: 14rem;
    background: var(--surface-inset);
    color: #bfffd8;
    font-size: 0.78rem;
  }

  .pack-key {
    color: var(--primary);
  }

  .action-row {
    gap: 0.3rem;
    flex-wrap: wrap;
  }

  .action-row button {
    min-height: 1.9rem;
    padding: 0.28rem 0.46rem;
    font-size: 0.58rem;
  }
</style>
