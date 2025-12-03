import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface SegmentBadgeProps {
    segment: string;
    className?: string;
}

export function SegmentBadge({ segment, className }: SegmentBadgeProps) {
    const getStyle = (seg: string) => {
        const s = seg.toUpperCase();
        // Inset Ring Style: bg-color-50 text-color-700 ring-1 ring-inset ring-color-600/20
        if (s.includes('BEHAVIORAL') || s.includes('SEGMENT A')) return 'bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-600/20';
        if (s.includes('FQHC') || s.includes('SEGMENT B')) return 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20';
        if (s.includes('URGENT') || s.includes('SEGMENT D')) return 'bg-purple-50 text-purple-700 ring-1 ring-inset ring-purple-600/20';
        if (s.includes('PRIMARY') || s.includes('SEGMENT E')) return 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/20';
        if (s.includes('HOSPITAL') || s.includes('SEGMENT F')) return 'bg-gray-50 text-gray-700 ring-1 ring-inset ring-gray-500/20';
        return 'bg-gray-50 text-gray-600 ring-1 ring-inset ring-gray-500/20'; // Other / Multi-Specialty
    };

    return (
        <span className={cn(
            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
            getStyle(segment),
            className
        )}>
            {segment}
        </span>
    );
}
