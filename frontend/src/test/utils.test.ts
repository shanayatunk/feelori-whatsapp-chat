import { describe, it, expect } from 'vitest';
import {
  validatePhoneNumber,
  formatPhoneNumber,
  formatCurrency,
  formatRelativeTime,
  truncateText,
  getInitials,
  debounce,
} from '@/lib/utils';

describe('Utility Functions', () => {
  describe('validatePhoneNumber', () => {
    it('validates correct phone numbers', () => {
      expect(validatePhoneNumber('+1234567890')).toBe(true);
      expect(validatePhoneNumber('+447700900123')).toBe(true);
      expect(validatePhoneNumber('+919876543210')).toBe(true);
    });

    it('rejects invalid phone numbers', () => {
      expect(validatePhoneNumber('123')).toBe(false);
      expect(validatePhoneNumber('abc')).toBe(false);
      expect(validatePhoneNumber('123-456-7890')).toBe(false);
      expect(validatePhoneNumber('')).toBe(false);
      expect(validatePhoneNumber('1234567890')).toBe(false); // Missing +
    });
  });

  describe('formatPhoneNumber', () => {
    it('formats phone numbers correctly', () => {
      expect(formatPhoneNumber('1234567890')).toBe('+1234567890');
      expect(formatPhoneNumber('+1234567890')).toBe('+1234567890');
      expect(formatPhoneNumber('123-456-7890')).toBe('+1234567890');
    });
  });

  describe('formatCurrency', () => {
    it('formats currency correctly', () => {
      expect(formatCurrency('29.99')).toBe('$29.99');
      expect(formatCurrency(100)).toBe('$100.00');
      expect(formatCurrency('0')).toBe('$0.00');
    });
  });

  describe('formatRelativeTime', () => {
    it('formats relative time correctly', () => {
      const now = new Date();
      const thirtySecondsAgo = new Date(now.getTime() - 30 * 1000);
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
      const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);
      const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);

      expect(formatRelativeTime(thirtySecondsAgo)).toBe('just now');
      expect(formatRelativeTime(fiveMinutesAgo)).toBe('5 minutes ago');
      expect(formatRelativeTime(twoHoursAgo)).toBe('2 hours ago');
      expect(formatRelativeTime(threeDaysAgo)).toBe('3 days ago');
    });
  });

  describe('truncateText', () => {
    it('truncates text correctly', () => {
      const longText = 'This is a very long text that should be truncated';
      expect(truncateText(longText, 20)).toBe('This is a very long ...');
      expect(truncateText('Short text', 20)).toBe('Short text');
    });
  });

  describe('getInitials', () => {
    it('gets initials correctly', () => {
      expect(getInitials('John Doe')).toBe('JD');
      expect(getInitials('Jane Mary Smith')).toBe('JM');
      expect(getInitials('SingleName')).toBe('S');
    });
  });

  describe('debounce', () => {
    it('debounces function calls', (done) => {
      let callCount = 0;
      const debouncedFunc = debounce(() => {
        callCount++;
      }, 100);

      // Call multiple times quickly
      debouncedFunc();
      debouncedFunc();
      debouncedFunc();

      // Should only be called once after delay
      setTimeout(() => {
        expect(callCount).toBe(1);
        done();
      }, 150);
    });
  });
});