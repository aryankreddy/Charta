import React, { useState } from 'react';
import { ChevronRight, Building2, MapPin } from 'lucide-react';
import { ScoreRing } from './ScoreRing';

interface Driver {
    label: string;
    value: string;
    color: string;
}

interface Clinic {
    id: string;
    name: string;
    tier: string;
    score: number;
    segment: string;
    state: string;
    revenue: string;
    volume: string;
    volume_unit: string;  // "patients" or "encounters"
    drivers: Driver[];
}

interface ClinicCardProps {
    clinic: Clinic;
    onClick: () => void;
}

export const ClinicCard: React.FC<ClinicCardProps> = ({ clinic, onClick }) => {
    const [showHighVolumeTooltip, setShowHighVolumeTooltip] = useState<number | null>(null);

    return (
        <div
            onClick={onClick}
            className="group bg-white rounded-lg p-4 mb-3 shadow-sm hover:shadow-md transition-all duration-200 border border-transparent hover:border-[#4A6741]/20 cursor-pointer flex items-center justify-between"
        >
            <div className="flex items-center gap-6 flex-1">
                <div className="flex-shrink-0">
                    <ScoreRing score={clinic.score} />
                </div>

                <div className="min-w-[200px]">
                    <h3 className="text-gray-800 font-semibold text-lg group-hover:text-[#4A6741] transition-colors truncate max-w-[300px]">
                        {clinic.name}
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                        <Building2 className="w-3 h-3" />
                        <span className="truncate max-w-[150px]">{clinic.segment}</span>
                        <span className="text-gray-300">•</span>
                        <MapPin className="w-3 h-3" />
                        <span>{clinic.state}</span>
                    </div>
                </div>

                <div className="flex gap-8 text-sm text-gray-600">
                    <div>
                        <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Revenue</div>
                        <div className="font-medium">{clinic.revenue}</div>
                    </div>
                    <div>
                        <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Volume</div>
                        <div className="font-medium">{clinic.volume}</div>
                    </div>
                </div>

                <div className="flex-1 flex gap-2 justify-end">
                    {clinic.drivers.slice(0, 2).map((driver, i) => (
                        <div
                            key={i}
                            className="relative"
                            onMouseEnter={(e) => {
                                e.stopPropagation();
                                if (driver.label.includes('High Volume')) {
                                    setShowHighVolumeTooltip(i);
                                }
                            }}
                            onMouseLeave={(e) => {
                                e.stopPropagation();
                                setShowHighVolumeTooltip(null);
                            }}
                        >
                            <span className={`text-xs px-2 py-1 rounded-full bg-gray-50 border border-gray-100 ${driver.color} whitespace-nowrap`}>
                                {driver.label}
                            </span>
                            {driver.label.includes('High Volume') && showHighVolumeTooltip === i && (
                                <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-gray-900 text-white rounded-lg shadow-xl z-50">
                                    <p className="font-bold mb-2 text-xs">High Volume Indicator:</p>
                                    <p className="text-xs mb-2">
                                        Organizations with <span className="font-semibold">verified volume exceeding 25,000 {clinic.volume_unit}</span> receive this designation.
                                    </p>
                                    <p className="text-xs mb-2">
                                        <span className="font-semibold">What this means:</span> {clinic.volume_unit === 'patients'
                                          ? 'Unique patients served annually (verified from HRSA UDS reports).'
                                          : 'Annual patient encounters/visits (from Medicare claims data).'}
                                    </p>
                                    <p className="text-xs mb-2">
                                        <span className="font-semibold">Why this matters:</span> High-volume organizations represent larger deal sizes and greater revenue potential from coding optimization.
                                    </p>
                                    <p className="text-xs text-white/80">
                                        Organizations with lower volume but multiple sites may receive "Multi-Site Network" instead.
                                    </p>
                                </div>
                            )}
                        </div>
                    ))}
                    {clinic.drivers.length > 2 && (
                        <span className="text-xs px-2 py-1 rounded-full bg-gray-50 text-gray-400">
                            +{clinic.drivers.length - 2}
                        </span>
                    )}
                </div>
            </div>

            <div className="ml-6 pl-6 border-l border-gray-100">
                <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-[#4A6741] transition-colors" />
            </div>
        </div>
    );
};
