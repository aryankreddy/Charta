"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Search, TrendingUp, Building2, Activity, ChevronLeft, ChevronRight, Info } from 'lucide-react';
import { ClinicDrawer } from '../components/ClinicDrawer';
import { Clinic } from '../types';

// Descriptive segment labels (migrated from Segment A-F in v11.0)
// Backend now uses: FQHC, Hospital, Private Practice, Behavioral Health, etc.
const getSegmentName = (segment: string): string => {
  // Segment names are already descriptive - no mapping needed
  return segment;
};

const TIERS = ['All Tiers', 'Tier 1', 'Tier 2', 'Tier 3'];
const DATA_STATUS = ['All Data', 'Verified Only'];
const TRACKS = ['All Tracks', 'Ambulatory', 'Behavioral', 'Post-Acute'];

export default function Dashboard() {
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [selectedClinic, setSelectedClinic] = useState<Clinic | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [segmentFilter, setSegmentFilter] = useState("All Segments");
  const [tierFilter, setTierFilter] = useState("All Tiers");
  const [statusFilter, setStatusFilter] = useState("All Data");
  const [trackFilter, setTrackFilter] = useState("All Tracks");
  const [driverFilter, setDriverFilter] = useState("All Tags");
  const [currentPage, setCurrentPage] = useState(1);
  const [showTierTooltip, setShowTierTooltip] = useState(false);
  const itemsPerPage = 50;

  useEffect(() => {
    fetch('/data/clinics.json')
      .then(res => res.json())
      .then(data => {
        setClinics(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load clinics:", err);
        setLoading(false);
      });
  }, []);

  const SEGMENTS = useMemo(() => {
    const uniqueSegments = Array.from(new Set(clinics.map(c => getSegmentName(c.segment)))).sort();
    return ['All Segments', ...uniqueSegments];
  }, [clinics]);

  // Extract unique driver tags from all clinics
  const AVAILABLE_DRIVERS = useMemo(() => {
    const allDrivers = new Set<string>();
    clinics.forEach(clinic => {
      clinic.drivers?.forEach(driver => {
        allDrivers.add(driver.label);
      });
    });
    return ['All Tags', ...Array.from(allDrivers).sort()];
  }, [clinics]);

  const filteredClinics = useMemo(() => {
    return clinics.filter(clinic => {
      const matchesSearch =
        clinic.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        clinic.id.includes(searchTerm) ||
        clinic.state.toLowerCase().includes(searchTerm.toLowerCase());

      const friendlySegment = getSegmentName(clinic.segment);
      const matchesSegment = segmentFilter === "All Segments" || friendlySegment === segmentFilter;
      const matchesTier = tierFilter === "All Tiers" || clinic.tier === tierFilter;
      const matchesStatus = statusFilter === "All Data" ? true : !clinic.is_projected_lift;
      
      // Track filtering - map display names to backend track names
      const clinicTrack = clinic.scoring_track || 'AMBULATORY';
      const matchesTrack = trackFilter === "All Tracks" ||
        (trackFilter === "Ambulatory" && clinicTrack === "AMBULATORY") ||
        (trackFilter === "Behavioral" && clinicTrack === "BEHAVIORAL") ||
        (trackFilter === "Post-Acute" && clinicTrack === "POST_ACUTE");

      // Driver tag filtering
      const matchesDriver = driverFilter === "All Tags" ||
        clinic.drivers?.some(driver => driver.label === driverFilter) ||
        false;

      return matchesSearch && matchesSegment && matchesTier && matchesStatus && matchesTrack && matchesDriver;
    });
  }, [clinics, searchTerm, segmentFilter, tierFilter, statusFilter, trackFilter, driverFilter]);

  const totalPages = Math.ceil(filteredClinics.length / itemsPerPage);
  const displayClinics = filteredClinics.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, segmentFilter, tierFilter, statusFilter, trackFilter, driverFilter]);

  const stats = {
    total: filteredClinics.length,
    tier1: filteredClinics.filter(c => c.tier === 'Tier 1').length
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-brand-600 animate-pulse mx-auto mb-4" />
          <p className="text-brand-700 font-medium">Accessing Intelligence Database...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 font-sans text-brand-900">
      <div className="bg-white border-b border-brand-200 sticky top-0 z-20 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center text-white font-bold shadow-sm">
                CH
              </div>
              <div>
                <h1 className="text-xl font-bold text-brand-900 tracking-tight">Charta Lead Database</h1>
                <p className="text-[10px] text-brand-600 mt-0.5">Top 5,000 organizations · 1.4M+ scored nationwide</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="px-4 py-2 bg-brand-100 rounded-lg border border-brand-200">
                <span className="text-xs text-brand-700 font-bold uppercase tracking-wider block">Tier 1 Leads</span>
                <span className="text-lg font-bold text-brand-900">{stats.tier1}</span>
              </div>
              <div
                className="relative"
                onMouseEnter={() => setShowTierTooltip(true)}
                onMouseLeave={() => setShowTierTooltip(false)}
              >
                <div className="p-2 bg-brand-100 rounded-lg border border-brand-200 cursor-help hover:bg-brand-200 transition-colors">
                  <Info className="w-4 h-4 text-brand-700" />
                </div>
                {showTierTooltip && (
                  <div className="absolute right-0 mt-2 p-4 bg-brand-900 text-white text-xs rounded-lg shadow-xl w-80 z-30">
                    <p className="font-bold mb-3 text-sm">Tier Breakdown</p>
                    <div className="space-y-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-bold bg-brand-200 text-brand-900 border border-brand-500">
                            Tier 1
                          </span>
                          <span className="font-semibold">Score ≥70</span>
                        </div>
                        <p className="text-white/80 text-[11px]">High-priority leads with strong pain signals, strategic fit, and immediate ROI potential. Focus sales efforts here.</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-bold bg-brand-100 text-brand-900 border border-brand-200">
                            Tier 2
                          </span>
                          <span className="font-semibold">Score 50-69</span>
                        </div>
                        <p className="text-white/80 text-[11px]">Qualified leads worth nurturing. Good fit but may need more discovery to validate opportunity size.</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-[10px] font-bold bg-brand-50 text-brand-700">
                            Tier 3
                          </span>
                          <span className="font-semibold">Score &lt;50</span>
                        </div>
                        <p className="text-white/80 text-[11px]">Low-priority leads. Monitor for changes in pain signals or strategic alignment before outreach.</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-700" />
              <input
                type="text"
                placeholder="Search organizations, NPIs, or states..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-brand-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all text-sm text-brand-900 placeholder-brand-700"
              />
            </div>
            <div className="flex gap-3">
              <select
                value={tierFilter}
                onChange={(e) => setTierFilter(e.target.value)}
                className="px-4 py-2.5 bg-white border border-brand-200 rounded-xl text-sm font-medium text-brand-900 focus:ring-2 focus:ring-brand-500 outline-none cursor-pointer hover:border-brand-500"
              >
                {TIERS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <select
                value={segmentFilter}
                onChange={(e) => setSegmentFilter(e.target.value)}
                className="px-4 py-2.5 bg-white border border-brand-200 rounded-xl text-sm font-medium text-brand-900 focus:ring-2 focus:ring-brand-500 outline-none cursor-pointer hover:border-brand-500"
              >
                {SEGMENTS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2.5 bg-white border border-brand-200 rounded-xl text-sm font-medium text-brand-900 focus:ring-2 focus:ring-brand-500 outline-none cursor-pointer hover:border-brand-500"
              >
                {DATA_STATUS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select
                value={trackFilter}
                onChange={(e) => setTrackFilter(e.target.value)}
                className="px-4 py-2.5 bg-white border border-brand-200 rounded-xl text-sm font-medium text-brand-900 focus:ring-2 focus:ring-brand-500 outline-none cursor-pointer hover:border-brand-500"
              >
                {TRACKS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <select
                value={driverFilter}
                onChange={(e) => setDriverFilter(e.target.value)}
                className="px-4 py-2.5 bg-white border border-brand-200 rounded-xl text-sm font-medium text-brand-900 focus:ring-2 focus:ring-brand-500 outline-none cursor-pointer hover:border-brand-500"
              >
                {AVAILABLE_DRIVERS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-white rounded-2xl shadow-sm border border-brand-200 overflow-hidden">
          <table className="min-w-full divide-y divide-brand-100">
            <thead className="bg-brand-100">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold text-brand-900 uppercase tracking-wider">Organization</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-brand-900 uppercase tracking-wider">Location</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-brand-900 uppercase tracking-wider">Tier</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-brand-900 uppercase tracking-wider">Score</th>
                <th className="px-6 py-4 text-right text-xs font-bold text-brand-900 uppercase tracking-wider">Verified Volume</th>
                <th className="px-6 py-4 text-right text-xs font-bold text-brand-900 uppercase tracking-wider">Est. Lift</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-brand-900 uppercase tracking-wider pl-8">Signals</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-100">
              {displayClinics.map((clinic) => (
                <tr
                  key={clinic.id}
                  onClick={() => setSelectedClinic(clinic)}
                  className="hover:bg-brand-100/50 cursor-pointer transition-colors group bg-white"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-brand-100 rounded-lg text-brand-700 group-hover:bg-brand-200 transition-colors">
                        <Building2 className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="font-bold text-brand-900">{clinic.name}</div>
                        <div className="text-xs text-brand-700 font-medium">{getSegmentName(clinic.segment)}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-brand-900 font-medium">{clinic.state}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap ${
                      clinic.tier === 'Tier 1' ? 'bg-brand-200 text-brand-900 border border-brand-500' :
                      clinic.tier === 'Tier 2' ? 'bg-brand-100 text-brand-900 border border-brand-200' :
                      'bg-brand-50 text-brand-700'
                    }`}>
                      {clinic.tier}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 ${
                      clinic.score >= 80 ? 'border-brand-600 text-brand-900 bg-brand-200' :
                      clinic.score >= 60 ? 'border-brand-500 text-brand-900 bg-brand-100' :
                      'border-brand-200 text-brand-700 bg-brand-50'
                    }`}>
                      {clinic.score}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="text-sm font-mono font-medium text-brand-900">{clinic.volume}</div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex flex-col items-end">
                      <div className="flex items-center gap-1 text-sm font-bold text-verified">
                        <TrendingUp className="w-3 h-3" />
                        {clinic.est_revenue_lift}
                      </div>
                      <span className={`text-[10px] font-medium ${
                        !clinic.is_projected_lift ? 'text-verified' : 'text-brand-700'
                      }`}>
                        {!clinic.is_projected_lift ? 'VERIFIED' : 'PROJECTED'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 pl-8">
                    <div className="flex flex-wrap gap-2">
                      {clinic.drivers.slice(0, 2).map((d, i) => (
                        <span key={i} className={`inline-flex items-center px-2 py-1 rounded-md text-[10px] font-bold border ${
                          d.color.includes('red') ? 'bg-red-50 text-pain border-red-200' :
                          d.color.includes('purple') ? 'bg-purple-50 text-whale border-purple-200' :
                          'bg-brand-100 text-brand-900 border-brand-200'
                        }`}>
                          {d.label}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="bg-white px-6 py-4 border-t border-brand-100 flex items-center justify-between">
            <div className="text-sm text-brand-700">
              Showing <span className="font-bold text-brand-900">{(currentPage-1)*itemsPerPage + 1}</span> to <span className="font-bold text-brand-900">{Math.min(currentPage*itemsPerPage, filteredClinics.length)}</span> of <span className="font-bold text-brand-900">{filteredClinics.length}</span> results
            </div>
            <div className="flex gap-2 items-center">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p-1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-brand-200 rounded-lg text-sm font-medium text-brand-900 hover:bg-brand-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
              <div className="flex items-center gap-2">
                <span className="text-sm text-brand-700">Page</span>
                <input
                  type="number"
                  min="1"
                  max={totalPages}
                  value={currentPage}
                  onChange={(e) => {
                    const page = parseInt(e.target.value);
                    if (page >= 1 && page <= totalPages) {
                      setCurrentPage(page);
                    }
                  }}
                  className="w-16 px-2 py-1.5 border border-brand-200 rounded-lg text-sm text-center font-medium text-brand-900 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                />
                <span className="text-sm text-brand-700">of {totalPages}</span>
              </div>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p+1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-brand-200 rounded-lg text-sm font-medium text-brand-900 hover:bg-brand-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <ClinicDrawer
        clinic={selectedClinic}
        onClose={() => setSelectedClinic(null)}
      />
    </div>
  );
}

