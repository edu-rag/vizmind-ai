'use client';

import { useEffect } from 'react';

export function useScrollBehavior() {
    useEffect(() => {
        // Enhanced smooth scrolling for anchor links
        const handleAnchorClick = (e: Event) => {
            const target = e.target as HTMLAnchorElement;
            if (target.tagName === 'A' && target.getAttribute('href')?.startsWith('#')) {
                e.preventDefault();
                const targetId = target.getAttribute('href')?.slice(1);
                const targetElement = document.getElementById(targetId || '');

                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                        inline: 'nearest'
                    });
                }
            }
        };

        // Add event listener for anchor links
        document.addEventListener('click', handleAnchorClick);

        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);

        // Observe elements with fade-in-up class
        const fadeElements = document.querySelectorAll('.fade-in-up');
        fadeElements.forEach(el => observer.observe(el));

        return () => {
            document.removeEventListener('click', handleAnchorClick);
            observer.disconnect();
        };
    }, []);
}
