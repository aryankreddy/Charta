import React from 'react';

interface DriverTagProps {
    label: string;
}

export function DriverTag({ label }: DriverTagProps) {
    if (!label) return null;

    // Determine icon/color based on content
    // Clean White Style: bg-white border border-slate-200 shadow-sm text-slate-700
    // We keep the text color but change the background to white/clean
    let bg = 'bg-white text-gray-700 border-gray-200';

    if (label.includes('🔥')) bg = 'bg-white text-orange-700 border-orange-200';
    if (label.includes('💰')) bg = 'bg-white text-green-700 border-green-200';
    if (label.includes('⚙️')) bg = 'bg-white text-blue-700 border-blue-200';
    if (label.includes('⚠️')) bg = 'bg-white text-red-700 border-red-200';

    return (
        <span className={`inline-flex items-center px-2 py-1 rounded text-[10px] font-semibold border shadow-sm ${bg}`}>
            {label}
        </span>
    );
}
