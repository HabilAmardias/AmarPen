<script lang="ts">
  export let value = '';
  export let label = '';

  const tone = (state: string): string => {
    if (['COMPLETED', 'VALIDATED', 'REVIEWED', 'FIXED', 'ACTIVE', 'SUCCESS', 'PUBLISHED', 'PASSED'].includes(state)) return 'success';
    if (['PAUSING', 'STOPPING', 'QUEUED', 'RUNNING', 'PARTIALLY_FIXED', 'PREVIEW', 'DRAFT', 'WARNING'].includes(state)) return 'warning';
    if (['FAILED', 'REJECTED', 'STOPPED', 'STILL_OPEN', 'EXTREME', 'CRITICAL', 'HIGH', 'BLOCKED', 'DISABLED', 'DENIED'].includes(state)) return 'danger';
    return '';
  };
</script>

<span class="badge {tone(value)}" data-testid="status-badge">{label || value || 'Unknown'}</span>
