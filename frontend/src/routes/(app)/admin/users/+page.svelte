<script lang="ts">
  import { onMount } from 'svelte';
  import { Key, LockKey, Plus, ShieldCheck, UserCircle, UsersThree } from 'phosphor-svelte';
  import { api, ApiError } from '../../../../lib/api/client';
  import type { User } from '../../../../lib/api/types';
  import ErrorView from '../../../../lib/components/ErrorView.svelte';
  import LoadingState from '../../../../lib/components/LoadingState.svelte';
  import StatusBadge from '../../../../lib/components/StatusBadge.svelte';

  const roleOptions = ['Administrator', 'Analyst', 'Reviewer', 'Viewer'];

  let users: User[] = [];
  let username = '';
  let roles = ['Analyst'];
  let temporaryPassword = '';
  let loading = true;
  let error = '';

  async function load() {
    loading = true;
    error = '';
    try {
      users = (await api.access.users()).items;
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to load users';
    } finally {
      loading = false;
    }
  }

  async function createUser() {
    error = '';
    try {
      const result = await api.access.createUser(username, roles);
      temporaryPassword = result.temporary_password;
      username = '';
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to create user';
    }
  }

  async function toggleDisabled(user: User) {
    try {
      await api.access.disable(user.id, !user.disabled, 'Administrator action');
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to change account state';
    }
  }

  async function resetMfa(user: User) {
    try {
      await api.access.resetMfa(user.id, 'Administrator recovery');
      await load();
      temporaryPassword = '';
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to reset MFA';
    }
  }

  async function resetPassword(user: User) {
    try {
      const result = await api.access.resetPassword(user.id, 'Administrator recovery');
      temporaryPassword = result.temporary_password;
      await load();
    } catch (cause) {
      error = cause instanceof ApiError ? cause.message : 'Unable to reset password';
    }
  }

  onMount(load);
</script>

<svelte:head><title>Users | AI-Assisted Pentest</title></svelte:head>

<div class="stack">
  <div class="grid two admin-grid">
    <form class="card stack" on:submit|preventDefault={createUser}>
      <div class="row" style="justify-content: space-between;">
        <span class="panel-kicker">PROVISION ACCOUNT</span>
        <Plus size={17} aria-hidden="true" class="text-green" />
      </div>
      <h2>New Operator</h2>
      <label>Username <input bind:value={username} required minlength="3" /></label>
      <fieldset class="role-fieldset">
        <legend>Roles</legend>
        <div class="role-options">
          {#each roleOptions as role}
            <label class="checkbox"><input type="checkbox" bind:group={roles} value={role} /> {role}</label>
          {/each}
        </div>
      </fieldset>
      <button type="submit"><UsersThree size={14} weight="bold" aria-hidden="true" /> Create account</button>
      <p class="small muted">Roles can be combined. Engagement authorization remains separate from platform administration.</p>
    </form>

    <div class="card stack security-note">
      <span class="panel-kicker">ACCESS POLICY</span>
      <h2>Account Controls</h2>
      <div class="policy-line"><ShieldCheck size={15} aria-hidden="true" /> Administrator actions are audited.</div>
      <div class="policy-line"><LockKey size={15} aria-hidden="true" /> Disabling an account revokes sessions and pauses initiated runs.</div>
      <div class="policy-line"><Key size={15} aria-hidden="true" /> MFA reset forces re-enrollment; recovery never exposes the old factor.</div>
    </div>
  </div>

  {#if error}<div class="alert error" role="alert">{error}</div>{/if}
  {#if temporaryPassword}
    <div class="alert success" role="status">
      Temporary password: <code>{temporaryPassword}</code>. Share it through an approved channel.
    </div>
  {/if}

  {#if loading}
    <LoadingState label="Loading users" />
  {:else if error && users.length === 0}
    <ErrorView title="Could not load users" message={error} onretry={load} />
  {:else}
    <div class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 0.5rem;">
        <span class="panel-kicker">ACCOUNT REGISTER</span>
        <span class="hud-meta"><span>{users.length} ACCOUNTS</span></span>
      </div>
      <table>
        <caption class="sr-only">Platform users</caption>
        <thead><tr><th scope="col">Operator</th><th scope="col">Roles</th><th scope="col">MFA</th><th scope="col">State</th><th scope="col">Recovery</th></tr></thead>
        <tbody>
          {#each users as user (user.id)}
            <tr>
              <td>
                <span class="user-cell"><UserCircle size={18} aria-hidden="true" /> {user.username}</span>
              </td>
              <td>
                <div class="role-list">
                  {#each user.roles as role}<span class="role-chip">{role}</span>{/each}
                </div>
              </td>
              <td>{user.totp_enabled ? 'Enrolled' : 'Pending'}</td>
              <td><StatusBadge value={user.disabled ? 'DISABLED' : 'ACTIVE'} /></td>
              <td>
                <div class="row recovery-actions">
                  <button type="button" class="secondary" on:click={() => toggleDisabled(user)}>{user.disabled ? 'Enable' : 'Disable'}</button>
                  <button type="button" class="secondary" on:click={() => resetMfa(user)}>Reset MFA</button>
                  <button type="button" class="secondary" on:click={() => resetPassword(user)}>Reset password</button>
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
  .admin-grid {
    align-items: start;
  }

  .role-fieldset {
    border: 1px solid var(--border);
    padding: 0.65rem;
  }

  .role-options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .checkbox {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    width: auto;
    font-size: 0.78rem;
  }

  .checkbox input {
    width: auto;
  }

  .security-note {
    min-height: 100%;
  }

  .policy-line {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.45rem 0;
    border-bottom: 1px dashed rgba(42, 74, 68, 0.35);
    color: var(--text-muted);
    font-size: 0.8rem;
  }

  .policy-line :global(svg) {
    color: var(--cyan);
    flex: 0 0 auto;
    margin-top: 0.1rem;
  }

  .user-cell {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--text);
  }

  .role-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
  }

  .role-chip {
    padding: 0.05rem 0.28rem;
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.56rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .recovery-actions {
    gap: 0.3rem;
  }

  .recovery-actions button {
    min-height: 1.9rem;
    padding: 0.28rem 0.48rem;
    font-size: 0.58rem;
  }
</style>
