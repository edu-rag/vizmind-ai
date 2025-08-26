'use client';

import { useEffect, useCallback } from 'react';
import { useAppStore } from '@/lib/store';
import { isTokenExpired, isTokenExpiringSoon } from '@/lib/utils';
import { toast } from 'sonner';

export interface UseAuthCheckOptions {
    /** Check interval in milliseconds (default: 60000 = 1 minute) */
    checkInterval?: number;
    /** Whether to show warning when token is expiring soon (default: true) */
    showExpirationWarning?: boolean;
    /** Minutes before expiration to show warning (default: 5) */
    warningMinutes?: number;
    /** Whether to automatically logout on expiration (default: true) */
    autoLogout?: boolean;
}

export function useAuthCheck(options: UseAuthCheckOptions = {}) {
    const {
        checkInterval = 180000, // 3 minutes
        showExpirationWarning = true,
        warningMinutes = 5,
        autoLogout = true,
    } = options;

    const { jwt, logout, isAuthenticated } = useAppStore();

    const checkTokenValidity = useCallback(() => {
        // Only check if user is authenticated and has a token
        if (!isAuthenticated || !jwt) {
            return;
        }

        // Check if token is expired
        if (isTokenExpired(jwt)) {
            console.warn('Token has expired. Logging out user.');
            if (autoLogout) {
                logout();
                toast.error('Your session has expired. Please log in again.');

                // Redirect to home page
                if (typeof window !== 'undefined') {
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                }
            }
            return;
        }

        // Check if token is expiring soon and show warning
        if (showExpirationWarning && isTokenExpiringSoon(jwt, warningMinutes)) {
            toast.warning(
                `Your session will expire in ${warningMinutes} minutes. Please save your work.`,
                {
                    duration: 10000, // Show for 10 seconds
                }
            );
        }
    }, [jwt, isAuthenticated, logout, autoLogout, showExpirationWarning, warningMinutes]);

    useEffect(() => {
        // Only set up interval if user is authenticated
        if (!isAuthenticated || !jwt) {
            return;
        }

        // Check immediately
        checkTokenValidity();

        // Set up periodic checking
        const interval = setInterval(checkTokenValidity, checkInterval);

        return () => {
            clearInterval(interval);
        };
    }, [jwt, isAuthenticated, checkTokenValidity, checkInterval]);

    // Return function to manually check token
    return {
        checkTokenValidity,
    };
}
