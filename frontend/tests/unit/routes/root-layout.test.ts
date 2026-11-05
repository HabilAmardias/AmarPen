import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import RootLayout from '../../../src/routes/+layout.svelte';

describe('root layout', () => {
  it('mounts the application shell slot', () => {
    render(RootLayout);
    expect(document.body).toBeTruthy();
    expect(document.querySelector('.page')).toBeNull();
  });
});
