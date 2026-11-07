<script lang="ts">
  import { FileCode, Plug, Robot, Scales, ShieldCheck, UsersThree } from 'phosphor-svelte';
</script>

<div class="stack">
  <div class="operation-header">
    <div>
      <span class="panel-kicker">CONTROL PLANE</span>
      <h1>Administration</h1>
      <p class="muted">Accounts, model boundaries, system instruction governance, and risk policy versions.</p>
    </div>
    <span class="badge success"><ShieldCheck size={12} aria-hidden="true" /> ADMINISTRATOR</span>
  </div>

  <nav class="tabs admin-tabs" aria-label="Administration sections">
    <a href="/admin/users"><UsersThree size={14} aria-hidden="true" /> Users</a>
    <a href="/admin/model-profiles"><Robot size={14} aria-hidden="true" /> Model profiles</a>
    <a href="/admin/prompts"><FileCode size={14} aria-hidden="true" /> System prompts</a>
    <a href="/admin/risk-policies"><Scales size={14} aria-hidden="true" /> Risk policies</a>
    <a href="/admin/mcp"><Plug size={14} aria-hidden="true" /> MCP registry</a>
  </nav>

  <slot />
</div>

<style>
  .admin-tabs a {
    gap: 0.35rem;
  }
</style>
