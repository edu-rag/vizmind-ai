'use client';

import { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  Loader2, 
  Shield,
  CheckCircle2,
  Lock,
  Zap,
  Globe
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { authenticateWithGoogle } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface AuthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function AuthDialog({ open, onOpenChange, onSuccess }: AuthDialogProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { setUser, setJWT } = useAppStore();

  const googleLogin = useGoogleLogin({
    onSuccess: async (response) => {
      setIsLoading(true);
      try {
        const result = await authenticateWithGoogle(response.access_token);
        
        if (result.error) {
          toast.error('Authentication failed');
          return;
        }

        if (result.data) {
          setJWT(result.data.access_token);
          setUser(result.data.user_info);
          toast.success('Successfully signed in!');
          onOpenChange(false);
          onSuccess?.();
        }
      } catch (error) {
        toast.error('Authentication failed');
        console.error('Auth error:', error);
      } finally {
        setIsLoading(false);
      }
    },
    onError: () => {
      toast.error('Google sign-in failed');
      setIsLoading(false);
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md p-0 overflow-hidden">
        <div className="relative">
          {/* Header */}
          <div className="spacing-mobile border-b border-border bg-gradient-to-r from-primary/5 to-primary/10">
            <div className="flex items-center space-x-3">
              <div className="flex-1">
                <DialogTitle className="text-responsive-xl font-semibold text-foreground">
                  Sign in to Continue
                </DialogTitle>
                <DialogDescription className="text-responsive-sm mt-1 text-muted-foreground">
                  Access your concept maps and create new ones with AI-powered insights
                </DialogDescription>
              </div>
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                <Shield className="h-6 w-6 text-primary" />
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="spacing-mobile space-y-6">
            {/* Features Preview */}
            <div className="space-y-4">
              <h3 className="text-responsive-sm font-medium text-foreground">
                What you'll get access to:
              </h3>
              <div className="grid gap-3">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                    <Zap className="h-4 w-4 text-green-600 dark:text-green-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-responsive-sm font-medium text-foreground">AI-Powered Analysis</p>
                    <p className="text-responsive-xs text-muted-foreground">Transform PDFs into interactive concept maps</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                    <Globe className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-responsive-sm font-medium text-foreground">Cloud Sync</p>
                    <p className="text-responsive-xs text-muted-foreground">Access your maps from anywhere</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                    <Lock className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-responsive-sm font-medium text-foreground">Secure & Private</p>
                    <p className="text-responsive-xs text-muted-foreground">Your data is encrypted and protected</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Google Sign In Button */}
            <div className="space-y-4">
              <Button
                onClick={() => googleLogin()}
                disabled={isLoading}
                className={cn(
                  "w-full touch-target text-responsive-sm font-medium",
                  "bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100",
                  "border border-gray-300 dark:border-gray-600",
                  "hover:bg-gray-50 dark:hover:bg-gray-800",
                  "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  "shadow-sm hover:shadow-md transition-all duration-200",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
                size="lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <svg className="mr-3 h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Continue with Google
                  </>
                )}
              </Button>

              {/* Security Notice */}
              <Card className="p-4 bg-muted/30 border-muted">
                <div className="flex items-start space-x-3">
                  <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <p className="text-responsive-sm font-medium text-foreground">
                      Secure Authentication
                    </p>
                    <p className="text-responsive-xs text-muted-foreground leading-relaxed">
                      We use Google's secure OAuth 2.0 protocol. We never store your password and only access basic profile information.
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Footer */}
            <div className="pt-4 border-t border-border">
              <p className="text-responsive-xs text-muted-foreground text-center leading-relaxed">
                By signing in, you agree to our{' '}
                <Button variant="link" className="text-primary hover:text-primary/80 p-0 h-auto text-responsive-xs">
                  Terms of Service
                </Button>{' '}
                and{' '}
                <Button variant="link" className="text-primary hover:text-primary/80 p-0 h-auto text-responsive-xs">
                  Privacy Policy
                </Button>
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}