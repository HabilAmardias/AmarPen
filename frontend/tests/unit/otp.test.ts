import { describe, expect, it } from 'vitest';
import { normalizeOtp, OTP_PATTERN } from '../../src/lib/otp';

describe('OTP helpers', () => {
  it('exports the anchored six-digit pattern', () => {
    expect(OTP_PATTERN).toBe('[0-9]{6}');
    const pattern = new RegExp(`^(?:${OTP_PATTERN})$`);
    expect(pattern.test('123456')).toBe(true);
    expect(pattern.test('12345')).toBe(false);
    expect(pattern.test('1234567')).toBe(false);
    expect(pattern.test('123 456')).toBe(false);
  });

  it('strips spaces and separators and caps at six digits', () => {
    expect(normalizeOtp('123 456')).toBe('123456');
    expect(normalizeOtp('12-34-56')).toBe('123456');
    expect(normalizeOtp('code: 987654')).toBe('987654');
    expect(normalizeOtp('1234567')).toBe('123456');
    expect(normalizeOtp('00 00 01')).toBe('000001');
  });
});
