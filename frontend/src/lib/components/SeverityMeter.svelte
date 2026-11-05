<script lang="ts">
  import type { Assessment } from '../api/types';

  export let assessment: Assessment | null = null;

  $: score = assessment?.cvss_score ?? 0;
  const segments = [1, 2, 3, 4, 5];
</script>

<div class="severity" aria-label="Assessment summary">
  <div class="item">
    <span class="small muted">Calculated CVSS</span>
    <strong class="readout">{assessment?.cvss_score ? assessment.cvss_score : '—'}</strong>
    <span class="small tone">{assessment?.cvss_rating ?? 'Not scored'}</span>
    <div class="segments" aria-hidden="true">
      {#each segments as segment}
        <span class:lit={score / 2 >= segment}></span>
      {/each}
    </div>
  </div>
  <div class="item">
    <span class="small muted">Manual reported severity</span>
    <strong class="readout manual">{assessment?.manual_severity || '—'}</strong>
    <span class="small">{assessment?.manual_severity ? 'Override active' : 'Not overridden'}</span>
    {#if assessment?.manual_reason}<span class="small muted clamp">{assessment.manual_reason}</span>{/if}
  </div>
  <div class="item">
    <span class="small muted">Business risk</span>
    <strong class="readout risk">{assessment?.business_band || 'Provisional'}</strong>
    {#if assessment?.business_likelihood}
      <span class="small">L{assessment.business_likelihood} × I{assessment.business_impact}</span>
    {:else}
      <span class="small muted">Awaiting matrix</span>
    {/if}
  </div>
  <div class="item">
    <span class="small muted">Confidence</span>
    <strong class="readout confidence">{assessment?.confidence ?? 'low'}</strong>
    <span class="small">{assessment?.provisional ? 'Provisional' : 'Reviewed'}</span>
  </div>
</div>

<style>
  .severity {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.65rem;
  }

  .item {
    position: relative;
    display: grid;
    gap: 0.18rem;
    padding: 0.7rem 0.75rem;
    border: 1px solid var(--border);
    background:
      linear-gradient(180deg, rgba(16, 28, 32, 0.86), rgba(6, 11, 14, 0.86));
    min-height: 6.4rem;
  }

  .item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 0.65rem;
    height: 1px;
    background: var(--primary);
    opacity: 0.7;
  }

  .readout {
    font-family: var(--font-display);
    font-size: 1.45rem;
    font-weight: 400;
    line-height: 1;
    color: var(--primary);
    text-shadow: 0 0 16px rgba(57, 255, 136, 0.12);
  }

  .manual {
    color: var(--amber);
    text-shadow: 0 0 16px rgba(255, 200, 87, 0.1);
  }

  .risk {
    color: var(--cyan);
    text-shadow: 0 0 16px rgba(69, 230, 255, 0.1);
  }

  .confidence {
    font-size: 1.15rem;
    text-transform: uppercase;
  }

  .tone {
    color: var(--text-muted);
  }

  .clamp {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .segments {
    display: flex;
    gap: 0.18rem;
    margin-top: 0.3rem;
  }

  .segments span {
    height: 0.18rem;
    flex: 1;
    background: var(--border);
  }

  .segments span.lit {
    background: var(--primary);
    box-shadow: 0 0 8px var(--glow-green);
  }

  @media (max-width: 900px) {
    .severity {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 560px) {
    .severity {
      grid-template-columns: 1fr;
    }
  }
</style>
