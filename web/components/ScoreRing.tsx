import React from 'react';

interface ScoreRingProps {
    score: number;
    size?: "sm" | "md" | "lg";
}

export const ScoreRing: React.FC<ScoreRingProps> = ({ score, size = "md" }) => {
    const radius = 18;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (score / 100) * circumference;

    let colorClass = "text-gray-400";
    if (score >= 80) colorClass = "text-[#4A6741]"; // Deep Sage
    else if (score >= 60) colorClass = "text-[#4A6741]/70"; // Light Sage

    const sizeClasses = {
        sm: "w-8 h-8 text-xs",
        md: "w-14 h-14 text-sm",
        lg: "w-16 h-16 text-lg"
    };

    return (
        <div className={`relative flex items-center justify-center ${sizeClasses[size]} group cursor-help`}>
            <svg className="transform -rotate-90 w-full h-full">
                <circle
                    className="text-gray-200"
                    strokeWidth="3"
                    stroke="currentColor"
                    fill="transparent"
                    r={radius}
                    cx="50%"
                    cy="50%"
                />
                <circle
                    className={`${colorClass} transition-all duration-1000 ease-out`}
                    strokeWidth="3"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="transparent"
                    r={radius}
                    cx="50%"
                    cy="50%"
                />
            </svg>
            <span className={`absolute font-bold ${colorClass}`}>
                {score}
            </span>

            {/* Exploded View Tooltip */}
            <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 w-48 bg-white shadow-xl rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none border border-gray-100">
                <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Score Drivers</div>
                <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                        <span className="text-gray-600">Economic Pain</span>
                        <span className={`font-medium ${score > 70 ? 'text-[#4A6741]' : 'text-gray-600'}`}>
                            {score > 70 ? 'High' : 'Moderate'}
                        </span>
                    </div>
                    <div className="flex justify-between text-xs">
                        <span className="text-gray-600">Strategic Fit</span>
                        <span className={`font-medium ${score > 50 ? 'text-[#4A6741]' : 'text-gray-600'}`}>
                            {score > 50 ? 'Strong' : 'Weak'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};
