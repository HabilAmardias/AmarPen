import { writable } from 'svelte/store';
import { api } from '../api/client';
import type { SessionInfo } from '../api/types';

export const session = writable<SessionInfo | null>(null);
export const sessionLoading = writable(false);

export async function loadSession(): Promise<SessionInfo | null> {
  sessionLoading.set(true);
  try {
    const value = await api.auth.session();
    session.set(value);
    return value;
  } catch {
    session.set(null);
    return null;
  } finally {
    sessionLoading.set(false);
  }
}

export async function logout(): Promise<void> {
  try {
    await api.auth.logout();
  } finally {
    session.set(null);
  }
}

export function hasRole(value: SessionInfo | null, ...roles: string[]): boolean {
  if (!value) return false;
  return value.user.roles.some((role) => roles.includes(role));
}
