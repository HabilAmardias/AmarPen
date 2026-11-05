<script lang="ts">
  import { onMount } from 'svelte';
  import { ArrowLeft, Bug, FileText, Flask, Gavel, Paperclip, ShieldCheck } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../../../lib/api/client';
  import type { Assessment, Evidence, Finding, RetestAttempt } from '../../../../../../lib/api/types';
  import ErrorView from '../../../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../../../lib/components/LoadingState.svelte';
  import SeverityMeter from '../../../../../../lib/components/SeverityMeter.svelte';
  import StatusBadge from '../../../../../../lib/components/StatusBadge.svelte';

  export let data: { id: string; findingId: string };

  let finding: Finding | null = null;
  let evidence: Evidence[] = [];
  let assessment: Assessment | null = null;
  let retests: RetestAttempt[] = [];
  let loading = true;
  let error = '';
  let notice = '';

  let vector = '';
  let rationale = '';
  let severity = 'High';
  let overrideReason = '';
  let likelihood = 4;
  let impact = 4;
  let businessRationale = '';
  let verdict = 'VALIDATED';
  let validationReason = '';
  let retestNotes = '';
  let retestFile: File | null = null;
  let retestOutcome = 'STILL_OPEN';
  let retestRationale = '';

  async function load() {
    loading = true;
    error = '';
    try {
      const detail = await api.findings.get(data.findingId);
      finding = detail.finding;
      evidence = detail.evidence;
      assessment = detail.assessment;
      retests = detail.retests;
      vector = assessment?.cvss_vector ?? '';
      rationale = Object.entries(assessment?.cvss_rationale ?? {}).map(([key, value]) => `${key}: ${value}`).join(', ');
      likelihood = assessment?.business_likelihood || 4;
      impact = assessment?.business_impact || 4;
      businessRationale = assessment?.business_rationale ?? '';
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load finding';
    } finally {
      loading = false;
    }
  }

  async function run(action: () => Promise<unknown>, message: string) {
    error = '';
    notice = '';
    try {
      await action();
      await load();
      notice = message;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Operation failed';
    }
  }

  function rationaleObject(): Record<string, string> {
    return rationale
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
      .reduce<Record<string, string>>((result, item) => {
        const [key, ...rest] = item.split(':');
        if (key && rest.length) result[key.trim()] = rest.join(':').trim();
        return result;
      }, {});
  }

  async function startRetest() {
    const current = finding;
    if (!current) return;
    await run(
      async () => {
        const attempt = await api.findings.startRetest(data.id, [current.id], retestNotes, `retest-${current.id}-${Date.now()}`);
        retests = [attempt, ...retests];
      },
      'Retest run created.'
    );
  }

  async function recordRetest(attemptId: string) {
    const current = finding;
    if (!current) return;
    await run(
      () =>
        api.findings.recordRetest(
          attemptId,
          current.id,
          retestOutcome,
          retestRationale,
          retestFile ?? undefined
        ),
      'Retest outcome recorded.'
    );
  }

  onMount(load);
</script>

<svelte:head><title>{finding?.title ?? 'Finding'} | AI-Assisted Pentest</title></svelte:head>

{#if loading}
  <LoadingState label="Loading finding" />
{:else if error && !finding}
  <ErrorView title="Finding unavailable" message={error} onretry={load} />
{:else if finding}
  <div class="stack">
    <div class="operation-header">
      <div>
        <a class="small back-link" href={`/engagements/${data.id}/findings`}><ArrowLeft size={13} aria-hidden="true" /> Back to findings</a>
        <span class="panel-kicker">FINDING WORKSTATION</span>
        <h1>{finding.title}</h1>
        <div class="hud-meta">
          <span>ASSETS <strong>{finding.affected_assets.join(', ') || 'NONE'}</strong></span>
          <span>VERSION <strong>V{finding.version}</strong></span>
          <span>CONFIDENCE <strong>{finding.confidence.toUpperCase()}</strong></span>
        </div>
      </div>
      <StatusBadge value={finding.state} />
    </div>

    {#if error}<div class="alert error" role="alert">{error}</div>{/if}
    {#if notice}<div class="alert success" role="status">{notice}</div>{/if}

    <SeverityMeter {assessment} />

    <div class="grid two workstation">
      <section class="card stack">
        <div class="row" style="justify-content: space-between;">
          <span class="panel-kicker">EVIDENCE CHAIN</span>
          <FileText size={17} aria-hidden="true" class="text-cyan" />
        </div>
        <h2>Claim + Evidence</h2>
        <p>{finding.description}</p>
        <dl class="facts">
          <dt>Expected</dt><dd>{finding.expected_behavior || 'Not recorded'}</dd>
          <dt>Actual</dt><dd>{finding.actual_behavior || 'Not recorded'}</dd>
          <dt>Impact</dt><dd>{finding.impact || 'Not recorded'}</dd>
          <dt>Remediation</dt><dd>{finding.remediation || 'Not recorded'}</dd>
          <dt>Confidence</dt><dd>{finding.confidence}</dd>
        </dl>

        <span class="hud-divider">ARTIFACTS</span>
        {#if evidence.length === 0}
          <p class="alert warning" role="status">No evidence is attached. Validation is blocked until evidence exists.</p>
        {:else}
          <ul class="evidence-list">
            {#each evidence as item (item.id)}
              <li>
                <a href={api.findings.evidenceUrl(item.id)}>
                  <Paperclip size={13} aria-hidden="true" /> {item.kind}
                </a>
                <span class="small muted">SHA-256 {item.sha256.slice(0, 16)}…</span>
              </li>
            {/each}
          </ul>
        {/if}

        <form
          class="stack validation-form"
          on:submit|preventDefault={() =>
            run(
              () => api.findings.validate(finding!.id, verdict, validationReason),
              'Validation verdict recorded.'
            )}
        >
          <span class="hud-divider">VALIDATION</span>
          <label>
            Verdict
            <select bind:value={verdict}>
              <option value="VALIDATED">Validated</option>
              <option value="REJECTED">Rejected</option>
              <option value="INCONCLUSIVE">Inconclusive</option>
            </select>
          </label>
          <label>Reason <input bind:value={validationReason} /></label>
          <button type="submit"><ShieldCheck size={14} weight="bold" aria-hidden="true" /> Record verdict</button>
        </form>
      </section>

      <section class="card stack">
        <div class="row" style="justify-content: space-between;">
          <span class="panel-kicker">ASSESSMENT CONSOLE</span>
          <Gavel size={17} aria-hidden="true" class="text-green" />
        </div>
        <h2>Scoring + Risk</h2>

        <form
          class="stack"
          on:submit|preventDefault={() =>
            run(() => api.scoring.cvss(finding!.id, vector, rationaleObject(), assessment?.version), 'CVSS assessment saved.')}
        >
          <span class="hud-divider">CVSS 4.0</span>
          <label>CVSS 4.0 vector <input bind:value={vector} placeholder="CVSS:4.0/AV:N/..." /></label>
          <label>Metric rationale <textarea bind:value={rationale} placeholder="AV: network, AC: low"></textarea></label>
          <button type="submit">Calculate CVSS</button>
        </form>

        <form
          class="stack"
          on:submit|preventDefault={() =>
            run(() => api.scoring.override(finding!.id, severity, overrideReason), 'Manual severity override recorded.')}
        >
          <span class="hud-divider">MANUAL OVERRIDE</span>
          <label>
            Severity
            <select bind:value={severity}>
              <option>Critical</option><option>High</option><option>Medium</option><option>Low</option><option>None</option>
            </select>
          </label>
          <label>Reason (required) <input bind:value={overrideReason} required /></label>
          <button type="submit" class="secondary">Override severity</button>
        </form>

        <form
          class="stack"
          on:submit|preventDefault={() =>
            run(() => api.scoring.businessRisk(finding!.id, likelihood, impact, businessRationale), 'Business risk saved.')}
        >
          <span class="hud-divider">BUSINESS RISK</span>
          <div class="grid two">
            <label>Likelihood (1–5) <input type="number" min="1" max="5" bind:value={likelihood} /></label>
            <label>Impact (1–5) <input type="number" min="1" max="5" bind:value={impact} /></label>
          </div>
          <label>Rationale <input bind:value={businessRationale} /></label>
          <button type="submit" class="secondary">Save business risk</button>
        </form>
      </section>
    </div>

    <section class="card stack">
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">RETEST PROTOCOL</span>
        <Flask size={17} aria-hidden="true" class="text-cyan" />
      </div>
      <h2>Selected-Finding Retest</h2>
      <p class="muted">Only this finding and necessary bounded prerequisites are rechecked. Original evidence is preserved.</p>

      <div class="grid two">
        <label>Remediation context <textarea bind:value={retestNotes}></textarea></label>
        <div class="stack retest-controls">
          <button type="button" on:click={startRetest}><Flask size={14} weight="bold" aria-hidden="true" /> Start selected-finding retest</button>
          <label>New evidence (required for validated outcomes) <input type="file" on:change={(event) => (retestFile = event.currentTarget.files?.[0] ?? null)} /></label>
          <label>
            Outcome
            <select bind:value={retestOutcome}>
              <option value="FIXED">Fixed</option>
              <option value="PARTIALLY_FIXED">Partially fixed</option>
              <option value="STILL_OPEN">Still open</option>
              <option value="INCONCLUSIVE">Inconclusive</option>
            </select>
          </label>
          <label>Rationale <input bind:value={retestRationale} /></label>
        </div>
      </div>

      {#if retests.length === 0}
        <p class="muted">No retest attempts recorded.</p>
      {:else}
        <div class="stack">
          {#each retests as attempt (attempt.id)}
            {@const outcomeEntries = Object.entries(attempt.outcomes) as Array<[string, string]>}
            <div class="retest-attempt">
              <div class="row" style="justify-content: space-between;">
                <strong><Bug size={13} aria-hidden="true" /> {attempt.id}</strong>
                <StatusBadge value={attempt.state} />
              </div>
              <p class="small muted">{attempt.notes || 'No notes'}</p>
              <ul class="outcome-list">
                {#each outcomeEntries as [findingId, outcome]}
                  <li>{findingId}: <StatusBadge value={outcome} /></li>
                {/each}
              </ul>
              <button type="button" class="secondary" on:click={() => recordRetest(attempt.id)}>Record outcome</button>
            </div>
          {/each}
        </div>
      {/if}

      <p class="small muted disposition">Latest validated disposition: <strong>{finding.latest_retest_outcome || 'Not retested'}</strong> ({finding.latest_retest_status || 'none'}).</p>
    </section>
  </div>
{/if}

<style>
  .back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    margin-bottom: 0.6rem;
    text-decoration: none;
  }

  .workstation {
    align-items: start;
  }

  .evidence-list {
    display: grid;
    gap: 0.35rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .evidence-list li {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--border);
    background: var(--surface-inset);
  }

  .evidence-list a {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    text-decoration: none;
  }

  .validation-form {
    margin-top: 0.35rem;
  }

  .retest-controls {
    align-content: start;
  }

  .retest-attempt {
    display: grid;
    gap: 0.45rem;
    padding: 0.75rem;
    border: 1px solid var(--border);
    background: rgba(6, 11, 14, 0.55);
  }

  .retest-attempt > .row strong {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.74rem;
  }

  .outcome-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0;
    padding: 0;
    list-style: none;
    color: var(--text-muted);
    font-size: 0.74rem;
  }

  .retest-attempt button {
    justify-self: start;
  }

  .disposition {
    margin: 0;
  }
</style>
