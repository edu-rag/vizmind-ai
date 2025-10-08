'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { Card } from '@/components/ui/card';
import { motion } from 'framer-motion';

export function MindMapSkeleton() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="w-full h-full p-6 space-y-4"
        >
            <Card className="p-8 space-y-6 gradient-ai-subtle border-2">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="space-y-2">
                        <Skeleton className="h-8 w-64" />
                        <Skeleton className="h-4 w-48" />
                    </div>
                    <Skeleton className="h-10 w-32" />
                </div>

                {/* Mind Map Nodes */}
                <div className="space-y-4">
                    <div className="flex items-center gap-4">
                        <Skeleton className="h-12 w-48 rounded-xl" />
                        <div className="flex-1 h-px bg-border" />
                        <Skeleton className="h-12 w-40 rounded-xl" />
                    </div>
                    <div className="flex items-center gap-4 ml-12">
                        <Skeleton className="h-12 w-40 rounded-xl" />
                        <div className="flex-1 h-px bg-border" />
                        <Skeleton className="h-12 w-36 rounded-xl" />
                    </div>
                    <div className="flex items-center gap-4 ml-24">
                        <Skeleton className="h-12 w-44 rounded-xl" />
                    </div>
                    <div className="flex items-center gap-4">
                        <Skeleton className="h-12 w-48 rounded-xl" />
                        <div className="flex-1 h-px bg-border" />
                        <Skeleton className="h-12 w-52 rounded-xl" />
                    </div>
                    <div className="flex items-center gap-4 ml-12">
                        <Skeleton className="h-12 w-36 rounded-xl" />
                    </div>
                </div>

                {/* Loading text */}
                <div className="text-center pt-4">
                    <Skeleton className="h-4 w-48 mx-auto" />
                </div>
            </Card>
        </motion.div>
    );
}

export function HistorySkeleton() {
    return (
        <div className="space-y-3 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                >
                    <Card className="p-4 space-y-3">
                        <Skeleton className="h-5 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                        <div className="flex gap-2">
                            <Skeleton className="h-6 w-16 rounded-full" />
                            <Skeleton className="h-6 w-20 rounded-full" />
                        </div>
                    </Card>
                </motion.div>
            ))}
        </div>
    );
}

export function DetailPanelSkeleton() {
    return (
        <div className="p-6 space-y-4">
            <div className="space-y-2">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-4 w-64" />
            </div>

            <div className="space-y-3 mt-6">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
            </div>

            <div className="space-y-3 mt-6">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/5" />
            </div>

            <div className="mt-6">
                <Skeleton className="h-10 w-full rounded-lg" />
            </div>
        </div>
    );
}
