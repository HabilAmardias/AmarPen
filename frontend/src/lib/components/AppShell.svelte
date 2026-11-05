<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import {
    Fingerprint,
    ListMagnifyingGlass,
    LockKey,
    Pulse,
    ShieldCheck,
    SignOut,
    SquaresFour,
    Terminal
  } from 'phosphor-svelte';
  import { logout } from '../stores/session';

  export let user: { username: string; roles: string[] } | null = null;

  let pathname = '';

  onMount(() => {
    pathname = window.location.pathname;
  });

  async function signOut() {
    await logout();
    await goto('/login');
  }
</script>

<a class="skip-link sr-only" href="#main-content">Skip to main content</a>

<div class="shell">
  <aside class="rail" aria-label="Platform command rail">
    <div class="rail-head">
      <a class="brand" href="/dashboard" aria-label="AI-Assisted Pentest dashboard">
        <span class="brand-mark" aria-hidden="true">
          <Terminal size={22} weight="bold" />
        </span>
        <span class="brand-copy">
          <strong>AI-Assisted Pentest</strong>
          <span class="brand-sub">AIPENTEST//OPS</span>
        </span>
      </a>
      <div class="rail-state" role="status">
        <span class="status-orb" aria-hidden="true"></span>
        <span>SYSTEM NOMINAL</span>
      </div>
    </div>

    <nav class="rail-nav" aria-label="Primary">
      <a class:active={pathname === '/dashboard'} href="/dashboard">
        <SquaresFour size={17} aria-hidden="true" />
        <span>Dashboard</span>
      </a>
      <a class:active={pathname.startsWith('/audit')} href="/audit">
        <ListMagnifyingGlass size={17} aria-hidden="true" />
        <span>Audit</span>
      </a>
      {#if user?.roles?.includes('Administrator')}
        <a class:active={pathname.startsWith('/admin')} href="/admin/users">
          <ShieldCheck size={17} aria-hidden="true" />
          <span>Administration</span>
        </a>
      {/if}
    </nav>

    <div class="rail-telemetry" aria-label="Local instance telemetry">
      <div class="telemetry-row">
        <span><LockKey size={13} aria-hidden="true" /> LOCAL NODE</span>
        <strong>ONLINE</strong>
      </div>
      <div class="telemetry-row">
        <span><Fingerprint size={13} aria-hidden="true" /> AUTH</span>
        <strong>MFA / TOTP</strong>
      </div>
      <div class="telemetry-row">
        <span><Pulse size={13} aria-hidden="true" /> CHANNEL</span>
        <strong>ENCRYPTED</strong>
      </div>
    </div>

    <div class="rail-foot">
      {#if user}
        <div class="operator">
          <div class="operator-id">
            <span class="operator-mark" aria-hidden="true">OP</span>
            <div>
              <strong>{user.username}</strong>
              <div class="role-list">
                {#each user.roles as role}
                  <span class="role-chip">{role}</span>
                {/each}
              </div>
            </div>
          </div>
          <button class="signout" type="button" on:click={signOut}>
            <SignOut size={15} aria-hidden="true" />
            <span>Sign out</span>
          </button>
        </div>
      {:else}
        <a class="button secondary" href="/login">Sign in</a>
      {/if}
      <div class="build">BUILD 0.1.0 / LOCAL</div>
    </div>
  </aside>

  <div class="shell-main">
    <header class="topbar">
      <div class="topbar-left">
        <span class="topbar-marker">SECURE CHANNEL</span>
        <span class="topbar-rule" aria-hidden="true"></span>
        <span class="topbar-note">ON-PREMISES ASSESSMENT CONSOLE</span>
      </div>
      <span class="topbar-status">
        <span class="status-orb" aria-hidden="true"></span>
        READY
      </span>
    </header>

    <main id="main-content" class="page">
      <slot />
    </main>
  </div>
</div>

<style>
  .skip-link:focus {
    position: fixed;
    top: 0.5rem;
    left: 0.5rem;
    z-index: 999;
    width: auto;
    height: auto;
    clip: auto;
    padding: 0.6rem 0.8rem;
    background: var(--primary);
    color: var(--on-primary);
  }

  .shell {
    display: grid;
    grid-template-columns: 252px minmax(0, 1fr);
    min-height: 100vh;
    position: relative;
    z-index: 1;
  }

  .rail {
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    padding: 1rem 0.9rem;
    background:
      linear-gradient(180deg, rgba(10, 18, 22, 0.98), rgba(5, 8, 10, 0.98));
    border-right: 1px solid var(--border);
    box-shadow: 12px 0 40px rgba(0, 0, 0, 0.26);
    z-index: 20;
  }

  .rail-head {
    display: grid;
    gap: 0.8rem;
    padding-bottom: 0.9rem;
    border-bottom: 1px solid var(--border);
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    text-decoration: none;
    color: var(--text);
  }

  .brand-mark {
    width: 2.35rem;
    height: 2.35rem;
    display: grid;
    place-items: center;
    color: var(--primary);
    border: 1px solid rgba(57, 255, 136, 0.38);
    background: rgba(57, 255, 136, 0.06);
    box-shadow: 0 0 18px rgba(57, 255, 136, 0.1);
    clip-path: polygon(0 0, calc(100% - 7px) 0, 100% 7px, 100% 100%, 7px 100%, 0 calc(100% - 7px));
  }

  .brand-copy {
    display: grid;
    gap: 0.08rem;
    line-height: 1.15;
  }

  .brand-copy strong {
    font-family: var(--font-display);
    font-size: 0.92rem;
    font-weight: 400;
    letter-spacing: 0.03em;
  }

  .brand-sub {
    color: var(--text-dim);
    font-size: 0.58rem;
    letter-spacing: 0.16em;
  }

  .rail-state,
  .topbar-status {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    color: var(--primary);
    font-size: 0.6rem;
    letter-spacing: 0.14em;
  }

  .rail-nav {
    display: grid;
    gap: 0.2rem;
  }

  .rail-nav a {
    display: flex;
    align-items: center;
    gap: 0.62rem;
    min-height: 2.5rem;
    padding: 0.55rem 0.65rem;
    border: 1px solid transparent;
    color: var(--text-muted);
    font-size: 0.7rem;
    letter-spacing: 0.09em;
    text-decoration: none;
    text-transform: uppercase;
    transition:
      color 150ms ease,
      background 150ms ease,
      border-color 150ms ease;
  }

  .rail-nav a:hover {
    color: var(--primary);
    background: rgba(57, 255, 136, 0.05);
    border-color: rgba(57, 255, 136, 0.18);
  }

  .rail-nav a.active {
    color: var(--primary);
    background: rgba(57, 255, 136, 0.07);
    border-color: rgba(57, 255, 136, 0.32);
    box-shadow: inset 2px 0 0 var(--primary);
  }

  .rail-telemetry {
    display: grid;
    gap: 0.35rem;
    padding: 0.7rem;
    border: 1px solid var(--border);
    background: rgba(5, 8, 10, 0.6);
    margin-top: auto;
  }

  .telemetry-row {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    color: var(--text-dim);
    font-size: 0.58rem;
    letter-spacing: 0.08em;
  }

  .telemetry-row span {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
  }

  .telemetry-row strong {
    color: var(--primary);
    font-weight: 500;
  }

  .rail-foot {
    display: grid;
    gap: 0.6rem;
    padding-top: 0.9rem;
    border-top: 1px solid var(--border);
  }

  .operator {
    display: grid;
    gap: 0.65rem;
  }

  .operator-id {
    display: flex;
    gap: 0.55rem;
    align-items: center;
  }

  .operator-mark {
    width: 1.9rem;
    height: 1.9rem;
    display: grid;
    place-items: center;
    border: 1px solid rgba(69, 230, 255, 0.3);
    background: rgba(69, 230, 255, 0.06);
    color: var(--cyan);
    font-size: 0.62rem;
    letter-spacing: 0.08em;
  }

  .operator-id strong {
    display: block;
    font-size: 0.76rem;
    font-weight: 500;
  }

  .role-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
    margin-top: 0.18rem;
  }

  .role-chip {
    padding: 0.04rem 0.24rem;
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.52rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .signout {
    min-height: 2.1rem;
    padding: 0.42rem 0.55rem;
    justify-content: flex-start;
    background: transparent;
    border-color: var(--border);
    color: var(--text-muted);
    box-shadow: none;
    clip-path: none;
    font-size: 0.64rem;
    letter-spacing: 0.08em;
  }

  .signout:hover {
    color: var(--danger);
    border-color: rgba(255, 77, 94, 0.38);
    background: rgba(255, 77, 94, 0.06);
    box-shadow: none;
  }

  .build {
    color: var(--text-dim);
    font-size: 0.54rem;
    letter-spacing: 0.1em;
  }

  .shell-main {
    min-width: 0;
  }

  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    min-height: 3.2rem;
    padding: 0.65rem clamp(1rem, 2.4vw, 2rem);
    border-bottom: 1px solid var(--border);
    background: rgba(5, 8, 10, 0.72);
    backdrop-filter: blur(8px);
    position: sticky;
    top: 0;
    z-index: 15;
  }

  .topbar-left {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    min-width: 0;
  }

  .topbar-marker {
    color: var(--primary);
    font-size: 0.6rem;
    letter-spacing: 0.14em;
    white-space: nowrap;
  }

  .topbar-rule {
    width: 1.6rem;
    height: 1px;
    background: var(--border-strong);
  }

  .topbar-note {
    color: var(--text-dim);
    font-size: 0.58rem;
    letter-spacing: 0.1em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .topbar-status {
    white-space: nowrap;
  }

  @media (max-width: 920px) {
    .shell {
      grid-template-columns: 1fr;
    }

    .rail {
      position: sticky;
      height: auto;
      padding: 0.7rem 0.9rem;
      border-right: 0;
      border-bottom: 1px solid var(--border);
      gap: 0.65rem;
    }

    .rail-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 0.55rem;
    }

    .rail-state {
      display: none;
    }

    .rail-nav {
      display: flex;
      gap: 0.3rem;
      overflow-x: auto;
      padding-bottom: 0.15rem;
    }

    .rail-nav a {
      min-height: 2.2rem;
      padding: 0.35rem 0.55rem;
      white-space: nowrap;
    }

    .rail-telemetry,
    .build {
      display: none;
    }

    .rail-foot {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      padding-top: 0;
      border-top: 0;
    }

    .operator {
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .operator-mark,
    .role-list {
      display: none;
    }

    .topbar {
      display: none;
    }
  }

  @media (max-width: 560px) {
    .brand-copy strong {
      font-size: 0.78rem;
    }

    .brand-sub {
      display: none;
    }

    .operator-id strong {
      max-width: 7rem;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .signout span {
      display: none;
    }

    .signout {
      width: 2.2rem;
      justify-content: center;
      padding: 0;
    }
  }
</style>
