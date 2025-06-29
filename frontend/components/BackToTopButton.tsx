'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowUp } from 'lucide-react';

export function BackToTopButton() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const toggleVisibility = () => {
            // Show button when page is scrolled down 300px
            if (window.pageYOffset > 300) {
                setIsVisible(true);
            } else {
                setIsVisible(false);
            }
        };

        window.addEventListener('scroll', toggleVisibility);

        return () => {
            window.removeEventListener('scroll', toggleVisibility);
        };
    }, []);

    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth',
        });
    };

    if (!isVisible) {
        return null;
    }

    return (
        <Button
            onClick={scrollToTop}
            size="icon"
            className="fixed bottom-6 right-6 z-50 rounded-full shadow-lg transition-all duration-300 hover:shadow-xl"
            aria-label="Back to top"
        >
            <ArrowUp className="h-4 w-4" />
        </Button>
    );
}
