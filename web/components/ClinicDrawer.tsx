import React, { useState, useEffect, useRef } from 'react';
import { X, TrendingUp, AlertTriangle, BarChart3, Info, Download, Copy, FileJson, FileSpreadsheet, Shield } from 'lucide-react';
import { Clinic } from '../types';
import { ScoreBreakdown } from './ScoreBreakdown';
import { downloadLeadAsJSON, downloadLeadAsCSV, copyLeadToClipboard } from '../lib/exportLead';

const SEGMENT_MAP: { [key: string]: string } = {
  'Segment A': 'Behavioral/Specialty',
  'Segment B': 'FQHC',
  'Segment C': 'Hospital',
  'Segment D': 'Urgent Care',
  'Segment E': 'Primary Care',
  'Segment F': 'Hospital',
  'Segment F - Hospital': 'Hospital'
};

const getSegmentName = (segment: string): string => {
  return SEGMENT_MAP[segment] || segment;
};

interface ClinicDrawerProps {
  clinic: Clinic | null;
  onClose: () => void;
}

export function ClinicDrawer({ clinic, onClose }: ClinicDrawerProps) {
  const [showLiftTooltip, setShowLiftTooltip] = useState(false);
  const [showCodingLiftTooltip, setShowCodingLiftTooltip] = useState(false);
  const [showDenialPreventionTooltip, setShowDenialPreventionTooltip] = useState(false);
  const [showUndercodingTooltip, setShowUndercodingTooltip] = useState(false);
  const [showPsychRiskTooltip, setShowPsychRiskTooltip] = useState(false);
  const [showConfidenceTooltip, setShowConfidenceTooltip] = useState(false);
  const [showScoreTooltip, setShowScoreTooltip] = useState(false);
  const [showRevenueTooltip, setShowRevenueTooltip] = useState(false);
  const [showVolumeTooltip, setShowVolumeTooltip] = useState(false);
  const [showHighVolumeTooltip, setShowHighVolumeTooltip] = useState<number | null>(null);
  const [showMipsTooltip, setShowMipsTooltip] = useState(false);
  const [showHpsaMuaTooltip, setShowHpsaMuaTooltip] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [exportToast, setExportToast] = useState<string | null>(null);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false);
      }
    };

    if (showExportMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showExportMenu]);

  if (!clinic) return null;

  const handleExport = async (type: 'json' | 'csv' | 'clipboard') => {
    try {
      if (type === 'json') {
        downloadLeadAsJSON(clinic);
        setExportToast('Lead exported as JSON');
      } else if (type === 'csv') {
        downloadLeadAsCSV(clinic);
        setExportToast('Lead exported as CSV');
      } else if (type === 'clipboard') {
        await copyLeadToClipboard(clinic);
        setExportToast('Lead copied to clipboard');
      }
      setShowExportMenu(false);
      setTimeout(() => setExportToast(null), 3000);
    } catch (error) {
      console.error('Export failed:', error);
      setExportToast('Export failed - please try again');
      setTimeout(() => setExportToast(null), 3000);
    }
  };

  const getConfidenceStatus = (confidence: string) => {
    const level = parseInt(confidence);
    if (level >= 70) return { label: 'High', color: 'bg-verified/10 text-verified border-verified' };
    if (level >= 40) return { label: 'Medium', color: 'bg-blue-50 text-blue-700 border-blue-200' };
    return { label: 'Low', color: 'bg-brand-100 text-brand-700 border-brand-200' };
  };

  const confidence = getConfidenceStatus(clinic.analysis.data_confidence);

  const getTierColor = (tier: string, score: number) => {
    if (score >= 90) return 'bg-emerald-700 text-white border-2 border-emerald-800';
    if (tier === 'Tier 1') return 'bg-brand-600 text-white';
    if (tier === 'Tier 2') return 'bg-brand-500 text-white';
    return 'bg-brand-700 text-white';
  };

  const getRevenueSourceTooltip = () => {
    const source = clinic.details.raw.revenue_source;
    let datasets = [];
    let description = '';

    if (source.includes('FQHC')) {
      datasets.push('FQHC Cost Reports (UDS)');
      description = 'Revenue from federally reported cost reports.';
    }
    if (source.includes('Hospital')) {
      datasets.push('Hospital Cost Reports (CMS)');
      description = 'Revenue from CMS hospital financial data.';
    }
    if (source.includes('HHA')) {
      datasets.push('Home Health Agency Reports');
      description = 'Revenue from home health agency cost reports.';
    }
    if (source.includes('Claims')) {
      datasets.push('Medicare Claims (Physician Utilization)');
      description = 'Aggregated from individual provider Medicare billing data via PECOS bridge (Individual NPI → Organization NPI).';
    }
    if (datasets.length === 0 || source.includes('Unknown')) {
      datasets.push('Estimated');
      description = 'Revenue estimated using industry benchmarks and available volume data.';
    }

    return (
      <div className="text-xs">
        <p className="font-bold mb-2">Data Source:</p>
        <ul className="space-y-1 mb-2">
          {datasets.map((ds, idx) => (
            <li key={idx}>• {ds}</li>
          ))}
        </ul>
        <p className="text-white/80 text-[10px]">{description}</p>
      </div>
    );
  };

  const getVolumeSourceTooltip = () => {
    const source = clinic.details.raw.volume_source;
    const volumeUnit = clinic.details.raw.volume_unit || clinic.volume_unit;
    let datasets = [];
    let description = '';
    let metricType = '';

    if (source.includes('UDS')) {
      datasets.push('HRSA UDS 2024 (Verified)');
      metricType = 'Unique Patients';
      description = 'Patient count from federally verified Uniform Data System reports. Represents unduplicated individuals served annually, matched via grant number.';
    }
    if (source.includes('Claims') || source.includes('Physician')) {
      datasets.push('Medicare Claims (Physician Utilization)');
      metricType = 'Patient Encounters/Visits';
      description = 'Encounter volume aggregated from individual provider Medicare claims data. Represents total visits (one patient may have multiple encounters). Rolled up from Individual NPIs to Organization NPI using PECOS reassignment bridge.';
    }
    if (source.includes('FQHC')) {
      datasets.push('FQHC Cost Reports');
      metricType = volumeUnit === 'patients' ? 'Unique Patients' : 'Encounters';
      description = 'Volume from federally reported cost reports.';
    }
    if (datasets.length === 0 || source.includes('Unknown')) {
      datasets.push('Estimated');
      metricType = 'Estimated Encounters';
      description = 'Volume estimated using revenue and industry benchmarks. Conservative assumption of encounters rather than unique patients.';
    }

    return (
      <div className="text-xs">
        <p className="font-bold mb-2">Data Source:</p>
        <ul className="space-y-1 mb-2">
          {datasets.map((ds, idx) => (
            <li key={idx}>• {ds}</li>
          ))}
        </ul>
        <p className="text-white/90 text-[11px] font-semibold mb-1">
          Metric Type: {metricType}
        </p>
        <p className="text-white/80 text-[10px]">{description}</p>
      </div>
    );
  };

  return (
    <>
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm transition-opacity z-40"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 w-[560px] bg-white border-l border-brand-200 shadow-2xl z-50 flex flex-col">
        <div className="p-6 border-b border-brand-100 bg-gradient-to-br from-brand-50 to-white">
          <div className="flex justify-between items-start mb-4">
            <div className="flex gap-2 flex-wrap">
              <span
                className={`inline-flex items-center px-4 py-1.5 rounded-xl text-sm font-bold ${getTierColor(
                  clinic.tier,
                  clinic.score
                )}`}
              >
                {clinic.score >= 90 ? 'High Volume' : clinic.tier}
              </span>

              <div
                className="relative"
                onMouseEnter={() => setShowConfidenceTooltip(true)}
                onMouseLeave={() => setShowConfidenceTooltip(false)}
              >
                <span
                  className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-sm font-medium border cursor-help ${confidence.color}`}
                >
                  {confidence.label} Confidence
                  <Info className="w-3 h-3" />
                </span>
                {showConfidenceTooltip && (
                  <div className="absolute left-0 top-full mt-2 w-72 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                    <p className="font-bold mb-2 text-xs">Data Confidence Score:</p>
                    <p className="text-xs mb-2">
                      Measures data completeness and reliability from verified federal sources (CMS, HRSA).
                    </p>
                    <p className="text-xs">
                      <span className="font-semibold">High (70%+):</span> Multi-source verified data.<br/>
                      <span className="font-semibold">Medium (40-69%):</span> Partial coverage, some estimates.<br/>
                      <span className="font-semibold">Low (&lt;40%):</span> Limited data, industry benchmarks used.
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative" ref={exportMenuRef}>
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  className="flex items-center gap-2 px-3 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  Export Lead
                </button>

                {showExportMenu && (
                  <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-brand-200 rounded-lg shadow-lg z-50">
                    <button
                      onClick={() => handleExport('clipboard')}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-brand-50 transition-colors text-left border-b border-brand-100"
                    >
                      <Copy className="w-4 h-4 text-brand-600" />
                      <div>
                        <div className="font-medium text-brand-900 text-sm">Copy to Clipboard</div>
                        <div className="text-xs text-brand-600">Formatted for CRM paste</div>
                      </div>
                    </button>
                    <button
                      onClick={() => handleExport('json')}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-brand-50 transition-colors text-left border-b border-brand-100"
                    >
                      <FileJson className="w-4 h-4 text-brand-600" />
                      <div>
                        <div className="font-medium text-brand-900 text-sm">Download JSON</div>
                        <div className="text-xs text-brand-600">For API integration</div>
                      </div>
                    </button>
                    <button
                      onClick={() => handleExport('csv')}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-brand-50 transition-colors text-left"
                    >
                      <FileSpreadsheet className="w-4 h-4 text-brand-600" />
                      <div>
                        <div className="font-medium text-brand-900 text-sm">Download CSV</div>
                        <div className="text-xs text-brand-600">For manual import</div>
                      </div>
                    </button>
                  </div>
                )}
              </div>

              <button
                onClick={onClose}
                className="p-2 hover:bg-brand-100 rounded-xl transition-colors"
              >
                <X className="w-5 h-5 text-brand-700" />
              </button>
            </div>
          </div>

          <h2 className="text-2xl font-bold text-brand-900 mb-3">
            {clinic.name}
          </h2>

          <div className="space-y-1 text-sm text-brand-700">
            <div className="flex items-center gap-2">
              <span className="font-medium">{getSegmentName(clinic.segment)}</span>
              <span className="text-brand-400">•</span>
              <span>{clinic.state}</span>
            </div>
            <div className="text-brand-600">{clinic.contact.address}</div>
            <div className="text-brand-600">
              {clinic.contact.phone || 'Phone: Available via NPPES lookup'}
            </div>
            <div className="text-brand-500 text-xs font-mono">NPI: {clinic.id}</div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <ScoreBreakdown clinic={clinic} />

          <section>
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-sm font-bold text-brand-900 uppercase tracking-wider">
                Intelligence Brief
              </h3>
              <div
                className="relative"
                onMouseEnter={() => setShowScoreTooltip(true)}
                onMouseLeave={() => setShowScoreTooltip(false)}
              >
                <Info className="w-4 h-4 text-brand-500 cursor-help" />
                {showScoreTooltip && (
                  <div className="absolute left-0 top-6 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                    <p className="font-bold mb-2 text-xs">Strategic Intelligence Report (AI-Generated):</p>
                    <p className="text-xs mb-2">
                      AI-synthesized assessment combining quantitative scoring with qualitative insights about this organization's fit and potential value.
                    </p>
                    <p className="text-xs text-white/80">
                      This is not a sales pitch - it's an objective evaluation of pain points, strategic alignment, and implementation considerations based on verified federal data sources.
                    </p>
                  </div>
                )}
              </div>
            </div>
            <div className="p-4 bg-brand-50 rounded-xl border border-brand-200">
              <p className="text-sm text-brand-900 leading-relaxed">
                {clinic.analysis.strategic_brief}
              </p>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-bold text-brand-900 uppercase tracking-wider mb-3">
              Evidence
            </h3>

            <div className="space-y-4">
              <div className="p-4 bg-white rounded-xl border border-brand-200 relative">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-verified" />
                  <span className="text-xs font-semibold text-brand-700 uppercase tracking-wider">
                    Total Opportunity
                  </span>
                  <div
                    className="relative ml-auto"
                    onMouseEnter={() => setShowLiftTooltip(true)}
                    onMouseLeave={() => setShowLiftTooltip(false)}
                  >
                    <Info className="w-4 h-4 text-brand-500 cursor-help" />
                    {showLiftTooltip && (
                      <div className="absolute right-0 top-6 w-72 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                        <p className="font-bold mb-2 text-xs">Total Opportunity Value:</p>
                        <p className="text-xs mb-2">
                          Combined value from revenue growth (coding optimization) and revenue defense (denial prevention).
                        </p>
                        <p className="text-xs text-white/80">
                          This represents the complete financial impact potential - both capturing missed revenue through better coding and preventing future losses from administrative denials.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-baseline gap-2 mb-3">
                  <span
                    className={`text-2xl font-bold ${
                      clinic.is_projected_lift ? 'text-brand-900' : 'text-verified'
                    }`}
                  >
                    {clinic.est_revenue_lift}
                  </span>
                  {!clinic.is_projected_lift && (
                    <span className="text-xs text-verified font-medium">✓ Verified</span>
                  )}
                </div>

                {/* Breakdown Section */}
                {clinic.opportunity_breakdown && (
                  <div className="mt-3 pt-3 border-t border-brand-100 space-y-2">
                    <div className="text-[10px] text-brand-600 uppercase tracking-wide mb-2 font-semibold">
                      Opportunity Breakdown
                    </div>

                    {/* Coding Optimization Row */}
                    <div
                      className="relative flex items-center justify-between py-2 px-3 bg-brand-50 rounded-lg"
                      onMouseEnter={() => setShowCodingLiftTooltip(true)}
                      onMouseLeave={() => setShowCodingLiftTooltip(false)}
                    >
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-3.5 h-3.5 text-verified" />
                        <span className="text-xs font-medium text-brand-900">Coding Optimization</span>
                        <Info className="w-3 h-3 text-brand-500 cursor-help" />
                      </div>
                      <span className="text-sm font-bold font-mono text-verified">
                        {clinic.opportunity_breakdown.coding_lift}
                      </span>
                      {showCodingLiftTooltip && (
                        <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                          <p className="font-bold mb-2 text-xs">Coding Optimization (Revenue Growth):</p>
                          <p className="text-xs mb-2">
                            Revenue recovery opportunity from improving coding accuracy and documentation to capture appropriate reimbursement.
                          </p>
                          {clinic.segment === 'Segment B' && clinic.opportunity_breakdown.payer_mix_applied && (
                            <p className="text-xs mb-2 text-yellow-300 font-semibold">
                              ⚠️ FQHC Adjustment: Conservative estimate based on Commercial/Payer Mix only. PPS revenue excluded.
                            </p>
                          )}
                          <p className="text-xs text-white/80">
                            {clinic.opportunity_breakdown.winning_status === 'WINNING'
                              ? 'This organization is already coding at or above benchmark. No additional coding lift identified.'
                              : clinic.is_projected_lift
                              ? 'Estimated using 5% industry benchmark when specific coding data is unavailable.'
                              : 'Calculated from verified coding gaps in Medicare claims data.'}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Denial Prevention Row */}
                    <div
                      className="relative flex items-center justify-between py-2 px-3 bg-brand-50 rounded-lg"
                      onMouseEnter={() => setShowDenialPreventionTooltip(true)}
                      onMouseLeave={() => setShowDenialPreventionTooltip(false)}
                    >
                      <div className="flex items-center gap-2">
                        <Shield className="w-3.5 h-3.5 text-brand-600" />
                        <span className="text-xs font-medium text-brand-900">Denial Prevention</span>
                        <Info className="w-3 h-3 text-brand-500 cursor-help" />
                      </div>
                      <span className="text-sm font-bold font-mono text-brand-600">
                        {clinic.opportunity_breakdown.denial_prevention}
                      </span>
                      {showDenialPreventionTooltip && (
                        <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                          <p className="font-bold mb-2 text-xs">Denial Prevention (Revenue Defense):</p>
                          <p className="text-xs mb-2">
                            Charta's AI-powered pre-bill review identifies and prevents up to 70% of denials before claims submission, protecting your revenue stream.
                          </p>
                          <p className="text-xs mb-2">
                            <span className="font-semibold">Industry Benchmark:</span> ~5% of revenue is typically lost to preventable claim denials.
                          </p>
                          <p className="text-xs text-white/80">
                            This value represents your protected revenue—the amount we help you defend through improved documentation and compliance before claims go out the door.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="text-xs text-brand-700 mt-3">
                  {clinic.lift_basis}
                </div>
              </div>

              {clinic.analysis.benchmarks.undercoding &&
                clinic.analysis.benchmarks.undercoding.value !== null && (
                  <div className={`p-4 bg-white rounded-xl border-2 ${
                    clinic.pain_label?.includes('Undercoding') && !clinic.pain_label?.includes('Therapy')
                      ? 'border-pain bg-pain/5'
                      : 'border-brand-200'
                  }`}>
                    <div className="flex items-center gap-2 mb-3">
                      <BarChart3 className={`w-4 h-4 ${
                        clinic.pain_label?.includes('Undercoding') && !clinic.pain_label?.includes('Therapy')
                          ? 'text-pain'
                          : clinic.analysis.benchmarks.undercoding.status === 'outperforming'
                          ? 'text-verified'
                          : 'text-brand-700'
                      }`} />
                      <span className="text-xs font-semibold text-brand-900 uppercase tracking-wider">
                        E&M Coding Performance (Medical)
                      </span>
                      {clinic.pain_label?.includes('Undercoding') && !clinic.pain_label?.includes('Therapy') && (
                        <span className="ml-2 text-[10px] font-bold text-pain uppercase px-2 py-0.5 bg-pain/10 rounded">
                          PRIMARY PAIN
                        </span>
                      )}
                      <div
                        className="relative ml-auto"
                        onMouseEnter={() => setShowUndercodingTooltip(true)}
                        onMouseLeave={() => setShowUndercodingTooltip(false)}
                      >
                        <Info className="w-4 h-4 text-brand-500 cursor-help" />
                        {showUndercodingTooltip && (
                          <div className="absolute right-0 top-6 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                            <p className="font-bold mb-2 text-xs">E&M Undercoding Ratio (Medical Visits):</p>
                            <p className="text-xs mb-2">
                              This ratio represents the percentage of E&M (Evaluation & Management) visits coded at Level 4 or 5 - the higher complexity/reimbursement codes used for primary care, urgent care, and general medical visits.
                            </p>
                            <p className="text-xs mb-2">
                              <span className="font-semibold">National Benchmark:</span> 45% of E&M visits are typically coded as Level 4/5.
                            </p>
                            <p className="text-xs text-white/80">
                              A ratio significantly below 45% suggests potential E&M undercoding - providers may be leaving revenue on the table. A ratio above 45% indicates strong documentation and appropriate coding practices.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-brand-700">Level 4/5 E&M Visits</span>
                        <span className="font-mono font-medium text-brand-900">
                          {(clinic.analysis.benchmarks.undercoding.value * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2.5 bg-brand-100 rounded-full overflow-hidden relative">
                        {/* 45% benchmark line */}
                        <div className="absolute left-[45%] top-0 h-full w-0.5 bg-brand-400 z-10" />
                        <div
                          className={`h-full rounded-full transition-all ${
                            clinic.analysis.benchmarks.undercoding.status === 'underperforming'
                              ? 'bg-pain'
                              : clinic.analysis.benchmarks.undercoding.status === 'outperforming'
                              ? 'bg-verified'
                              : 'bg-brand-500'
                          }`}
                          style={{
                            width: `${clinic.analysis.benchmarks.undercoding.value * 100}%`,
                          }}
                        />
                      </div>
                      <div className="flex justify-between text-[10px] text-brand-500 mt-1">
                        <span>0%</span>
                        <span className="font-semibold" style={{marginLeft: '-2%'}}>45% benchmark</span>
                        <span>100%</span>
                      </div>
                      <p
                        className={`text-xs font-medium mt-2 ${
                          clinic.analysis.benchmarks.undercoding.status === 'underperforming'
                            ? 'text-pain'
                            : clinic.analysis.benchmarks.undercoding.status === 'outperforming'
                            ? 'text-verified'
                            : 'text-brand-700'
                        }`}
                      >
                        {clinic.analysis.benchmarks.undercoding.status === 'underperforming'
                          ? `${(45 - clinic.analysis.benchmarks.undercoding.value * 100).toFixed(1)}% below benchmark - E&M undercoding detected`
                          : `${(clinic.analysis.benchmarks.undercoding.value * 100 - 45).toFixed(1)}% above benchmark - Strong E&M documentation`}
                      </p>
                    </div>
                  </div>
                )}

              {clinic.analysis.benchmarks.psych_audit_risk && (
                <div className={`p-4 bg-white rounded-xl border-2 ${
                  clinic.pain_label?.includes('Therapy')
                    ? 'border-pain bg-pain/5'
                    : 'border-brand-200'
                }`}>
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart3 className={`w-4 h-4 ${
                      clinic.pain_label?.includes('Therapy')
                        ? clinic.analysis.benchmarks.psych_audit_risk.status === 'severe'
                          ? 'text-pain'
                          : 'text-pain'
                        : clinic.analysis.benchmarks.psych_audit_risk.status === 'severe'
                        ? 'text-pain'
                        : clinic.analysis.benchmarks.psych_audit_risk.status === 'elevated'
                        ? 'text-yellow-500'
                        : 'text-verified'
                    }`} />
                    <span className="text-xs font-semibold text-brand-900 uppercase tracking-wider">
                      Therapy Coding Performance (Behavioral)
                    </span>
                    {clinic.pain_label?.includes('Therapy') && (
                      <span className="ml-2 text-[10px] font-bold text-pain uppercase px-2 py-0.5 bg-pain/10 rounded">
                        PRIMARY PAIN
                      </span>
                    )}
                    <div
                      className="relative ml-auto"
                      onMouseEnter={() => setShowPsychRiskTooltip(true)}
                      onMouseLeave={() => setShowPsychRiskTooltip(false)}
                    >
                      <Info className="w-4 h-4 text-brand-500 cursor-help" />
                      {showPsychRiskTooltip && (
                        <div className="absolute right-0 top-6 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                          <p className="font-bold mb-2 text-xs">Therapy Coding Performance (Behavioral Health):</p>
                          <p className="text-xs mb-2">
                            This ratio represents the percentage of therapy sessions coded at high-complexity levels (90834+, 90837+) - the higher reimbursement codes for psychotherapy.
                          </p>
                          <p className="text-xs mb-2">
                            <span className="font-semibold">National Benchmark:</span> 50% of therapy sessions are typically coded at high-complexity levels.
                          </p>
                          <p className="text-xs mb-2">
                            <span className="font-semibold">Low ratio (&lt;30%):</span> Suggests conservative therapy coding - potential revenue leakage from underdocumenting session complexity.
                          </p>
                          <p className="text-xs text-white/80">
                            <span className="font-semibold">High ratio (&gt;75%):</span> Indicates elevated audit risk - organizations may face increased scrutiny from payers requiring documentation validation.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-brand-700">High-Complexity Therapy Sessions</span>
                      <span className="font-mono font-medium text-brand-900">
                        {(clinic.analysis.benchmarks.psych_audit_risk.value * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2.5 bg-brand-100 rounded-full overflow-hidden relative">
                      {/* 50% benchmark line */}
                      <div className="absolute left-1/2 top-0 h-full w-0.5 bg-brand-400 z-10" />
                      <div
                        className={`h-full rounded-full ${
                          clinic.analysis.benchmarks.psych_audit_risk.value <= 0.30
                            ? 'bg-pain'
                            : clinic.analysis.benchmarks.psych_audit_risk.value >= 0.75
                            ? 'bg-pain'
                            : clinic.analysis.benchmarks.psych_audit_risk.value >= 0.60
                            ? 'bg-yellow-500'
                            : 'bg-verified'
                        }`}
                        style={{
                          width: `${clinic.analysis.benchmarks.psych_audit_risk.value * 100}%`,
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-brand-500 mt-1">
                      <span>0%</span>
                      <span className="font-semibold">50% benchmark</span>
                      <span>100%</span>
                    </div>
                    <p className={`text-xs font-medium mt-2 ${
                      clinic.analysis.benchmarks.psych_audit_risk.value <= 0.30
                        ? 'text-pain'
                        : clinic.analysis.benchmarks.psych_audit_risk.value >= 0.75
                        ? 'text-pain'
                        : clinic.analysis.benchmarks.psych_audit_risk.value >= 0.60
                        ? 'text-yellow-600'
                        : 'text-verified'
                    }`}>
                      {clinic.analysis.benchmarks.psych_audit_risk.value <= 0.30
                        ? `${(50 - clinic.analysis.benchmarks.psych_audit_risk.value * 100).toFixed(1)}% below benchmark - Conservative coding suggests revenue leakage`
                        : clinic.analysis.benchmarks.psych_audit_risk.value >= 0.75
                        ? `${(clinic.analysis.benchmarks.psych_audit_risk.value * 100 - 50).toFixed(1)}% above benchmark - Elevated audit risk`
                        : clinic.analysis.benchmarks.psych_audit_risk.value >= 0.60
                        ? `${(clinic.analysis.benchmarks.psych_audit_risk.value * 100 - 50).toFixed(1)}% above benchmark - Moderate audit exposure`
                        : 'Balanced therapy coding - Appropriate documentation'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>

          <section>
            <h3 className="text-sm font-bold text-brand-900 uppercase tracking-wider mb-3">
              Key Signals
            </h3>
            <div className="space-y-2">
              {clinic.drivers.map((driver, idx) => (
                <div
                  key={idx}
                  className="relative flex items-center gap-3 p-3 bg-white rounded-xl border border-brand-200"
                  onMouseEnter={() => {
                    if (driver.label.includes('High Volume')) {
                      setShowHighVolumeTooltip(idx);
                    }
                  }}
                  onMouseLeave={() => setShowHighVolumeTooltip(null)}
                >
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: driver.color }}
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-brand-900">{driver.label}</div>
                    {driver.value && (
                      <div className="text-xs text-brand-700 mt-0.5">{driver.value}</div>
                    )}
                  </div>
                  {driver.label.includes('High Volume') && showHighVolumeTooltip === idx && (
                    <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                      <p className="font-bold mb-2 text-xs">High Volume Indicator:</p>
                      <p className="text-xs mb-2">
                        Organizations with <span className="font-semibold">verified volume exceeding 25,000 {clinic.volume_unit}</span> receive this designation.
                      </p>
                      <p className="text-xs mb-2">
                        <span className="font-semibold">Why this matters:</span> High-volume organizations represent larger deal sizes and greater revenue potential from coding optimization.
                      </p>
                      <p className="text-xs text-white/80">
                        Volume is verified from HRSA UDS reports or aggregated Medicare claims data. Organizations with lower volume but multiple sites may receive "Multi-Site Network" instead. The threshold balances deal size with implementation complexity.
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {clinic.analysis.gaps && clinic.analysis.gaps.length > 0 && (
            <section>
              <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-semibold text-yellow-900 mb-2">
                      Missing Data
                    </div>
                    <ul className="text-sm text-yellow-800 space-y-1">
                      {clinic.analysis.gaps.map((gap, idx) => (
                        <li key={idx}>• {gap}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </section>
          )}

          <section>
            <h3 className="text-sm font-bold text-brand-900 uppercase tracking-wider mb-3">
              Organization Metrics
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div
                className="relative p-4 bg-white rounded-xl border border-brand-200"
                onMouseEnter={() => setShowRevenueTooltip(true)}
                onMouseLeave={() => setShowRevenueTooltip(false)}
              >
                <div className="flex items-center gap-1 text-xs text-brand-700 mb-1">
                  Revenue
                  <Info className="w-3 h-3 cursor-help" />
                </div>
                <div className="text-lg font-bold text-brand-900 font-mono">{clinic.revenue}</div>
                {showRevenueTooltip && (
                  <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                    {getRevenueSourceTooltip()}
                  </div>
                )}
              </div>
              <div
                className="relative p-4 bg-white rounded-xl border border-brand-200"
                onMouseEnter={() => setShowVolumeTooltip(true)}
                onMouseLeave={() => setShowVolumeTooltip(false)}
              >
                <div className="flex items-center gap-1 text-xs text-brand-700 mb-1">
                  {clinic.volume_unit === 'patients' ? 'Unique Patients' : 'Annual Encounters'}
                  <Info className="w-3 h-3 cursor-help" />
                </div>
                <div className="text-lg font-bold text-brand-900 font-mono">{clinic.volume}</div>
                <div className="text-[10px] text-brand-500 mt-1 uppercase tracking-wide">
                  {clinic.volume_unit === 'patients' ? 'Unduplicated' : 'Total Visits'}
                </div>
                {showVolumeTooltip && (
                  <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                    {getVolumeSourceTooltip()}
                  </div>
                )}
              </div>
            </div>
          </section>

          {(clinic.details.raw.avg_mips_score !== null || clinic.details.raw.is_hpsa || clinic.details.raw.is_mua) && (
            <section>
              <h3 className="text-sm font-bold text-brand-900 uppercase tracking-wider mb-3">
                Quality & Strategic Designations
              </h3>
              <div className="space-y-3">
                {clinic.details.raw.avg_mips_score !== null && (
                  <div
                    className="relative p-4 bg-white rounded-xl border border-brand-200"
                    onMouseEnter={() => setShowMipsTooltip(true)}
                    onMouseLeave={() => setShowMipsTooltip(false)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1">
                        <span className="text-xs font-semibold text-brand-700 uppercase tracking-wider">
                          MIPS Quality Score
                        </span>
                        <Info className="w-3 h-3 text-brand-500 cursor-help" />
                      </div>
                      <span
                        className={`text-xl font-bold font-mono ${
                          clinic.details.raw.avg_mips_score > 80
                            ? 'text-verified'
                            : clinic.details.raw.avg_mips_score < 50
                            ? 'text-pain'
                            : 'text-brand-900'
                        }`}
                      >
                        {clinic.details.raw.avg_mips_score.toFixed(1)}
                      </span>
                    </div>
                    <div className="text-xs text-brand-700">
                      {clinic.details.raw.avg_mips_score > 80 ? (
                        <span>High-performing organization (+5pts Strategic Fit)</span>
                      ) : clinic.details.raw.avg_mips_score < 50 ? (
                        <span>Performance challenges present revenue recovery opportunity (+5pts Strategic Fit)</span>
                      ) : (
                        <span>Standard performance</span>
                      )}
                      {clinic.details.raw.mips_clinician_count && (
                        <span className="block mt-1 text-brand-600">
                          {clinic.details.raw.mips_clinician_count} reporting clinician
                          {clinic.details.raw.mips_clinician_count > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    {showMipsTooltip && (
                      <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                        <p className="font-bold mb-2 text-xs">MIPS Quality Performance:</p>
                        <p className="text-xs mb-2">
                          <span className="font-semibold">Why this matters:</span> MIPS scores reveal organizational quality and compliance readiness. High performers (80+) demonstrate strong documentation practices—ideal for optimization. Low performers (&lt;50) face payment penalties and represent revenue recovery opportunities.
                        </p>
                        <p className="text-xs text-white/80">
                          <span className="font-semibold">Source:</span> CMS MIPS Public Reporting (2023). Organization scores averaged across all reporting clinicians matched via NPI.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {(clinic.details.raw.is_hpsa || clinic.details.raw.is_mua) && (
                  <div
                    className="relative p-4 bg-white rounded-xl border border-brand-200"
                    onMouseEnter={() => setShowHpsaMuaTooltip(true)}
                    onMouseLeave={() => setShowHpsaMuaTooltip(false)}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-semibold text-brand-700 uppercase tracking-wider">
                        Underserved Area Designations
                      </span>
                      <Info className="w-3 h-3 text-brand-500 cursor-help" />
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {clinic.details.raw.is_hpsa && (
                        <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-verified/10 text-verified border border-verified">
                          HPSA Designated
                        </span>
                      )}
                      {clinic.details.raw.is_mua && (
                        <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-verified/10 text-verified border border-verified">
                          MUA Designated
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-brand-700 mt-2">
                      {clinic.details.raw.county_name && clinic.state && (
                        <span>
                          {clinic.details.raw.county_name} County, {clinic.state}
                        </span>
                      )}
                      <span className="block mt-1">
                        Strategic market opportunity (+5pts Strategic Fit)
                      </span>
                    </div>
                    {showHpsaMuaTooltip && (
                      <div className="absolute left-0 top-full mt-2 w-80 p-3 bg-brand-900 text-white rounded-lg shadow-xl z-50">
                        <p className="font-bold mb-2 text-xs">Federal Shortage Designations:</p>
                        <p className="text-xs mb-2">
                          <span className="font-semibold">Why this matters:</span> HPSA/MUA organizations serve high-need populations and qualify for federal incentives. They often have mission-driven leadership, stable funding, and alignment with value-based care—making them receptive to technology that improves outcomes while capturing revenue.
                        </p>
                        <p className="text-xs text-white/80">
                          <span className="font-semibold">Source:</span> HRSA Data Warehouse. County-level matching via ZIP code + state to federal designation files.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>
          )}

        </div>

        <div className="p-4 border-t border-brand-200 bg-brand-50">
          <div className="text-xs text-center text-brand-700 space-y-1">
            <div>
              {!clinic.is_projected_lift ? (
                <span className="text-verified font-medium">
                  ✓ Verified opportunity based on CMS/HRSA data
                </span>
              ) : (
                <span>Projected opportunity · {clinic.lift_basis}</span>
              )}
            </div>
            <div className="text-brand-600 text-[10px]">
              Displaying top 5,000 organizations from 1.4M+ scored nationwide
            </div>
          </div>
        </div>
      </div>

      {exportToast && (
        <div className="fixed bottom-6 right-6 bg-brand-900 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-3 animate-in slide-in-from-bottom-4">
          <div className="w-2 h-2 bg-verified rounded-full"></div>
          <span className="font-medium">{exportToast}</span>
        </div>
      )}
    </>
  );
}
