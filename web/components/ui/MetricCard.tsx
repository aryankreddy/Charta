import React from 'react';
import { Info } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface MetricCardProps {
    label: string;
    score: number;
    description?: string;
    className?: string;
}

export function MetricCard({ label, score, description, className }: MetricCardProps) {
    // Color logic based on score
    const getColor = (s: number) => {
        if (s >= 80) return 'bg-accent-hot';
        if (s >= 50) return 'bg-accent-warm';
        return 'bg-gray-400';
    };

    return (
        <div className={cn("p-4 bg-white rounded-lg border border-gray-100 shadow-sm", className)}>
            <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</span>
                    {description && (
                        <div className="group relative">
                            <Info className="w-3.5 h-3.5 text-gray-400 cursor-help" />
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                {description}
                                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                            </div>
                        </div>
                    )}
                </div>
                <span className="text-lg font-bold text-gray-900">{score.toFixed(0)}</span>
            </div>

            {/* Progress Bar */}
            <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                    className={cn("h-full rounded-full transition-all duration-500", getColor(score))}
                    style={{ width: `${score}%` }}
                />
            </div>
        </div>
    );
}
