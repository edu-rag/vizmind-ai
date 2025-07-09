'use client';

import { useState } from 'react';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Loader2,
  Shield,
  CheckCircle2,
  Lock,
  Globe,
  Sparkles
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

  const handleGoogleLogin = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      toast.error('Authentication failed');
      return;
    }

    setIsLoading(true);
    try {
      const result = await authenticateWithGoogle(credentialResponse.credential);

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
  };

  const handleGoogleError = () => {
    toast.error('Google sign-in failed');
    setIsLoading(false);
  };

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
                    <Sparkles className="h-4 w-4 text-green-600 dark:text-green-400" />
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
              <div className="w-full">
                {isLoading ? (
                  <div className="w-full h-11 flex items-center justify-center border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900">
                    <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                    <span className="text-responsive-sm font-medium text-gray-900 dark:text-gray-100">
                      Signing in...
                    </span>
                  </div>
                ) : (
                  <GoogleLogin
                    onSuccess={handleGoogleLogin}
                    onError={handleGoogleError}
                    theme="outline"
                    size="large"
                    width="100%"
                    text="continue_with"
                    shape="rectangular"
                  />
                )}
              </div>

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