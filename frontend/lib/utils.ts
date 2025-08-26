import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// JWT utility functions
export function decodeJWT(token: string): any | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
}

export function isTokenExpired(token: string | null): boolean {
  if (!token) return true;

  const decoded = decodeJWT(token);
  if (!decoded || !decoded.exp) return true;

  const currentTime = Math.floor(Date.now() / 1000);
  return decoded.exp < currentTime;
}

export function getTokenExpirationTime(token: string | null): Date | null {
  if (!token) return null;

  const decoded = decodeJWT(token);
  if (!decoded || !decoded.exp) return null;

  return new Date(decoded.exp * 1000);
}

// Check if token will expire soon (within specified minutes)
export function isTokenExpiringSoon(token: string | null, withinMinutes: number = 5): boolean {
  if (!token) return true;

  const decoded = decodeJWT(token);
  if (!decoded || !decoded.exp) return true;

  const currentTime = Math.floor(Date.now() / 1000);
  const warningTime = decoded.exp - (withinMinutes * 60);

  return currentTime >= warningTime;
}
