import { get } from 'svelte/store';
import { describe, expect, it } from 'vitest';
import { hasRole, loadSession, logout, session } from '../../../src/lib/stores/session';

describe('session store', () => {
  it('loads and exposes the current session', async () => {
    const value = await loadSession();
    expect(value?.user.username).toBe('admin');
    expect(get(session)?.user.username).toBe('admin');
  });

  it('checks roles and clears the session on logout', async () => {
    await loadSession();
    expect(hasRole(get(session), 'Administrator')).toBe(true);
    expect(hasRole(get(session), 'Viewer')).toBe(false);
    await logout();
    expect(get(session)).toBeNull();
  });
});
