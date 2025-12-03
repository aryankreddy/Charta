import React, { useState } from 'react';
import { Clinic } from '../types';
import { Info } from 'lucide-react';

interface ScoreBreakdownProps {
  clinic: Clinic;
}

export function ScoreBreakdown({ clinic }: ScoreBreakdownProps) {
  const [hoveredSection, setHoveredSection] = useState<string | null>(null);

  const painScore = clinic.analysis.raw_scores.pain.total;
  const fitScore = clinic.analysis.raw_scores.fit.total;
  const strategyScore = clinic.analysis.raw_scores.strategy.total;
  const track = clinic.scoring_track || 'AMBULATORY';

  // Calculate Fit bonuses (MIPS + HPSA/MUA can add up to +10 pts beyond base 30)
  const fitBase = clinic.analysis.raw_scores.fit.alignment +
                  clinic.analysis.raw_scores.fit.complexity +
                  clinic.analysis.raw_scores.fit.risk;
  const fitBonus = fitScore - fitBase;
  const hasFitBonus = fitBonus > 0.1; // Only show if bonus > 0.1 to avoid floating point issues

  // Helper to get pain description based on pain label
  const getPainDescription = (painLabel: string) => {
    // Map pain labels to descriptions
    if (painLabel.includes('Therapy Undercoding')) {
      return {
        description: 'Conservative therapy coding patterns indicating potential revenue recovery opportunities from undercoded behavioral health sessions.',
        matters: 'Organizations coding therapy conservatively (low % of high-complexity sessions) may have documentation supporting higher reimbursement. Similar to E&M undercoding, this represents verified revenue on the table.'
      };
    }
    if (painLabel.includes('Audit Risk') || painLabel.includes('Therapy Audit Risk')) {
      return {
        description: 'Aggressive therapy coding patterns creating compliance exposure and potential recoupment risk.',
        matters: 'Organizations with high % of max-complexity therapy sessions face audit scrutiny from payers. Risk mitigation and compliance protection are primary value propositions.'
      };
    }
    if (painLabel.includes('Margin Pressure')) {
      return {
        description: 'Operating margin analysis and financial sustainability risks.',
        matters: 'Post-acute organizations with margin compression are motivated buyers seeking operational efficiency and better reimbursement capture.'
      };
    }
    if (painLabel.includes('Undercoding')) {
      return {
        description: 'Revenue recovery opportunities from E&M undercoding and compliance risks.',
        matters: 'Higher pain = immediate ROI for AI chart review. Organizations with coding gaps or audit exposure are motivated buyers. Revenue leakage is measured via undercoding ratio (% of Level 4/5 E&M codes vs national benchmark).'
      };
    }
    // Default fallback
    return {
      description: 'Economic pain signals indicating revenue optimization or compliance opportunities.',
      matters: 'Organizations with higher pain scores represent motivated buyers with clear ROI pathways.'
    };
  };

  // Track-specific configuration
  const getTrackConfig = () => {
    // Use dynamic pain_label if available, otherwise fall back to track-based defaults
    const painLabel = clinic.pain_label ||
      (track === 'BEHAVIORAL' ? 'Economic Pain (Audit Risk)' :
       track === 'POST_ACUTE' ? 'Economic Pain (Margin Pressure)' :
       'Economic Pain (Revenue Leakage)');

    const painDesc = getPainDescription(painLabel);

    const trackLabel = track === 'BEHAVIORAL' ? 'Behavioral Health' :
                       track === 'POST_ACUTE' ? 'Post-Acute' :
                       'Ambulatory';

    return {
      label: trackLabel,
      painLabel: painLabel,
      painDescription: painDesc.description,
      painMatters: painDesc.matters
    };
  };

  const trackConfig = getTrackConfig();

  const getPainTooltip = () => {
    return (
      <div className="absolute z-10 mt-2 p-3 bg-brand-900 text-white text-xs rounded-lg shadow-lg w-96 left-0">
        <p className="font-bold mb-2">{trackConfig.painLabel} (Max 40 pts)</p>
        <p className="mb-2 text-white/90">
          <span className="font-semibold">What it measures:</span> {trackConfig.painDescription}
        </p>
        <p className="mb-2 text-white/90">
          <span className="font-semibold">Why it matters:</span> {trackConfig.painMatters}
        </p>
        <div className="mt-3 pt-2 border-t border-white/20">
          <p className="font-semibold mb-1 text-[10px] uppercase text-white/70">Scoring Breakdown:</p>
          <ul className="space-y-1 text-white/80">
            {clinic.analysis.score_reasoning.pain.map((reason, idx) => (
              <li key={idx}>• {reason}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const getFitTooltip = () => {
    // Determine which bonuses are active
    const mipsScore = clinic.details.raw.avg_mips_score;
    const hasMipsBonus = mipsScore !== null && (mipsScore > 80 || mipsScore < 50);
    const hasHpsaMuaBonus = clinic.details.raw.is_hpsa || clinic.details.raw.is_mua;

    return (
      <div className="absolute z-10 mt-2 p-3 bg-brand-900 text-white text-xs rounded-lg shadow-lg w-96 left-0">
        <p className="font-bold mb-2">Strategic Fit (Base: 30 pts + Up to 10 Bonus)</p>
        <p className="mb-2 text-white/90">
          <span className="font-semibold">What it measures:</span> Alignment with Charta's proven segments (FQHC, Behavioral Health) and operational readiness.
        </p>
        <p className="mb-2 text-white/90">
          <span className="font-semibold">Base scoring (30 pts):</span> Segment alignment (15) + Organization complexity (10) + Tech/Risk flags (5)
        </p>
        <p className="mb-2 text-white/90">
          <span className="font-semibold">Bonus points (up to 10):</span>
        </p>
        <ul className="ml-3 mb-2 text-white/80 text-[11px] space-y-0.5">
          <li className={hasMipsBonus ? 'text-verified' : 'text-white/50'}>
            {hasMipsBonus ? '✓' : '○'} MIPS Quality Bonus (+5): {
              mipsScore !== null
                ? mipsScore > 80
                  ? `High performer (${mipsScore.toFixed(1)})`
                  : mipsScore < 50
                  ? `Distressed performer (${mipsScore.toFixed(1)})`
                  : `Standard (${mipsScore.toFixed(1)})`
                : 'Not applicable'
            }
          </li>
          <li className={hasHpsaMuaBonus ? 'text-verified' : 'text-white/50'}>
            {hasHpsaMuaBonus ? '✓' : '○'} HPSA/MUA Bonus (+5): {
              hasHpsaMuaBonus
                ? `${clinic.details.raw.is_hpsa ? 'HPSA' : ''}${clinic.details.raw.is_hpsa && clinic.details.raw.is_mua ? '/' : ''}${clinic.details.raw.is_mua ? 'MUA' : ''} designated`
                : 'Not in shortage area'
            }
          </li>
        </ul>
        <div className="mt-3 pt-2 border-t border-white/20">
          <p className="font-semibold mb-1 text-[10px] uppercase text-white/70">Component Breakdown:</p>
          <ul className="space-y-1 text-white/80">
            {clinic.analysis.score_reasoning.fit.map((reason, idx) => (
              <li key={idx}>• {reason}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const getStrategyTooltip = () => {
    const volumeThreshold = track === 'BEHAVIORAL' ? '10k' : '25k';
    const volumeNote = track === 'BEHAVIORAL' 
      ? 'Behavioral health practices have lower visit volumes due to longer therapy sessions. Volume >10k patients indicates significant scale.'
      : `Large organizations justify higher CAC, longer implementation, and executive engagement. Volume >${volumeThreshold} patients = multi-million dollar annual contract potential.`;
    
    return (
      <div className="absolute z-10 mt-2 p-3 bg-brand-900 text-white text-xs rounded-lg shadow-lg w-96 left-0">
        <p className="font-bold mb-2">Strategic Value (Max 30 pts)</p>
        <p className="mb-2 text-white/90">
          <span className="font-semibold">What it measures:</span> Deal size potential (revenue + volume scale) and expansion opportunities.
        </p>
        <p className="mb-2 text-white/90">
          <span className="font-semibold">Why it matters:</span> {volumeNote}
        </p>
        <div className="mt-3 pt-2 border-t border-white/20">
          <p className="font-semibold mb-1 text-[10px] uppercase text-white/70">Scoring Breakdown:</p>
          <ul className="space-y-1 text-white/80">
            {clinic.analysis.score_reasoning.strategy.map((reason, idx) => (
              <li key={idx}>• {reason}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-brand-900 uppercase tracking-wider">
          ICP Score Breakdown
        </h3>
        <span className="text-[10px] font-bold text-white bg-brand-600 px-2 py-1 rounded-md uppercase tracking-wide">
          {trackConfig.label} Track
        </span>
      </div>
      <div className="space-y-4">
        <div
          className="relative"
          onMouseEnter={() => setHoveredSection('pain')}
          onMouseLeave={() => setHoveredSection(null)}
        >
          <div className="flex justify-between items-center text-xs mb-1">
            <div className="flex items-center gap-1">
              <span className="font-semibold text-brand-900">{trackConfig.painLabel}</span>
              <Info className="w-3 h-3 text-brand-500 cursor-help" />
            </div>
            <span className="font-mono font-bold text-pain">{painScore.toFixed(1)}/40 pts</span>
          </div>
          <div className="h-3 bg-brand-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-pain rounded-full transition-all"
              style={{ width: `${(painScore / 40) * 100}%` }}
            />
          </div>
          {hoveredSection === 'pain' && getPainTooltip()}
        </div>

        <div
          className="relative"
          onMouseEnter={() => setHoveredSection('fit')}
          onMouseLeave={() => setHoveredSection(null)}
        >
          <div className="flex justify-between items-center text-xs mb-1">
            <div className="flex items-center gap-1">
              <span className="font-semibold text-brand-900">Strategic Fit</span>
              <Info className="w-3 h-3 text-brand-500 cursor-help" />
              {hasFitBonus && (
                <span className="text-[9px] font-bold text-verified bg-verified/10 px-1.5 py-0.5 rounded uppercase">
                  +{fitBonus.toFixed(1)} bonus
                </span>
              )}
            </div>
            <span className="font-mono font-bold text-brand-600">
              {fitScore.toFixed(1)}/{hasFitBonus ? '40' : '30'} pts
            </span>
          </div>
          <div className="h-3 bg-brand-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full transition-all"
              style={{ width: `${Math.min(100, (fitScore / (hasFitBonus ? 40 : 30)) * 100)}%` }}
            />
          </div>
          {hoveredSection === 'fit' && getFitTooltip()}
        </div>

        <div
          className="relative"
          onMouseEnter={() => setHoveredSection('strategy')}
          onMouseLeave={() => setHoveredSection(null)}
        >
          <div className="flex justify-between items-center text-xs mb-1">
            <div className="flex items-center gap-1">
              <span className="font-semibold text-brand-900">Strategic Value</span>
              <Info className="w-3 h-3 text-brand-500 cursor-help" />
            </div>
            <span className="font-mono font-bold text-verified">{strategyScore.toFixed(1)}/30 pts</span>
          </div>
          <div className="h-3 bg-brand-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-verified rounded-full transition-all"
              style={{ width: `${(strategyScore / 30) * 100}%` }}
            />
          </div>
          {hoveredSection === 'strategy' && getStrategyTooltip()}
        </div>

        <div className="pt-3 border-t border-brand-200">
          <div className="flex justify-between items-center">
            <span className="text-sm font-bold text-brand-900">Total Score</span>
            <span className="text-2xl font-bold text-brand-900">{clinic.score}/100</span>
          </div>
        </div>
      </div>
    </section>
  );
}
