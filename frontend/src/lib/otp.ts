export const OTP_PATTERN = '[0-9]{6}';

export function normalizeOtp(value: string): string {
  return value.replace(/\D/g, '').slice(0, 6);
}

export function applyOtpInput(event: Event): string {
  const input = event.currentTarget as HTMLInputElement;
  const normalized = normalizeOtp(input.value);
  if (input.value !== normalized) {
    input.value = normalized;
  }
  return normalized;
}
