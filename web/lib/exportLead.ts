/**
 * Lead Export Module
 *
 * Prepares clinic data for CRM export (HubSpot, Salesforce, etc.)
 * This abstraction makes it easy to integrate with any CRM later.
 */

import { Clinic } from '../types';

export interface ExportedLead {
  // Company/Organization Info
  company: {
    name: string;
    npi: string;
    phone: string;
    address: string;
    state: string;
    segment: string;
  };

  // Deal/Opportunity Info
  opportunity: {
    dealName: string;
    estimatedValue: string;
    isVerified: boolean;
    tier: string;
    stage: 'New Lead' | 'Qualified' | 'High Priority';
  };

  // Scoring & Intelligence
  intelligence: {
    icpScore: number;
    painScore: number;
    fitScore: number;
    strategyScore: number;
    dataConfidence: string;
    strategicBrief: string;
  };

  // Key Metrics
  metrics: {
    revenue: string;
    volume: string;
    estimatedLift: string;
    avgMipsScore: number | null;
    isHpsa: boolean;
    isMua: boolean;
    undercodingRatio: number | null;
  };

  // Sales Intelligence
  signals: {
    primaryDriver: string;
    keyDrivers: Array<{ label: string; value: string }>;
    gaps: string[];
    reasoning: {
      pain: string[];
      fit: string[];
      strategy: string[];
    };
  };
}

/**
 * Converts a Clinic object to a standardized export format
 */
export function prepareLeadForExport(clinic: Clinic): ExportedLead {
  // Determine deal stage based on score and tier
  let stage: 'New Lead' | 'Qualified' | 'High Priority' = 'New Lead';
  if (clinic.score >= 80 || clinic.tier === 'Tier 1') {
    stage = 'High Priority';
  } else if (clinic.score >= 60) {
    stage = 'Qualified';
  }

  return {
    company: {
      name: clinic.name,
      npi: clinic.id,
      phone: clinic.contact.phone || '',
      address: clinic.contact.address,
      state: clinic.state,
      segment: clinic.segment,
    },

    opportunity: {
      dealName: `${clinic.name} - AI Chart Review Opportunity`,
      estimatedValue: clinic.est_revenue_lift,
      isVerified: !clinic.is_projected_lift,
      tier: clinic.tier,
      stage,
    },

    intelligence: {
      icpScore: clinic.score,
      painScore: clinic.analysis.raw_scores.pain.total,
      fitScore: clinic.analysis.raw_scores.fit.total,
      strategyScore: clinic.analysis.raw_scores.strategy.total,
      dataConfidence: clinic.analysis.data_confidence,
      strategicBrief: clinic.analysis.strategic_brief,
    },

    metrics: {
      revenue: clinic.revenue,
      volume: clinic.volume,
      estimatedLift: clinic.est_revenue_lift,
      avgMipsScore: clinic.details.raw.avg_mips_score,
      isHpsa: clinic.details.raw.is_hpsa,
      isMua: clinic.details.raw.is_mua,
      undercodingRatio: clinic.details.raw.undercoding_ratio,
    },

    signals: {
      primaryDriver: clinic.primary_driver,
      keyDrivers: clinic.drivers.map(d => ({
        label: d.label,
        value: d.value,
      })),
      gaps: clinic.analysis.gaps,
      reasoning: clinic.analysis.score_reasoning,
    },
  };
}

/**
 * Formats lead data as JSON for download
 */
export function downloadLeadAsJSON(clinic: Clinic): void {
  const exportData = prepareLeadForExport(clinic);
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${clinic.name.replace(/[^a-z0-9]/gi, '_')}_lead_export.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Formats lead data as CSV for download
 */
export function downloadLeadAsCSV(clinic: Clinic): void {
  const lead = prepareLeadForExport(clinic);

  const rows = [
    // Header
    ['Field', 'Value'],

    // Company Info
    ['Company Name', lead.company.name],
    ['NPI', lead.company.npi],
    ['Phone', lead.company.phone],
    ['Address', lead.company.address],
    ['State', lead.company.state],
    ['Segment', lead.company.segment],

    // Deal Info
    ['Deal Name', lead.opportunity.dealName],
    ['Estimated Value', lead.opportunity.estimatedValue],
    ['Verified Opportunity', lead.opportunity.isVerified ? 'Yes' : 'No'],
    ['Tier', lead.opportunity.tier],
    ['Stage', lead.opportunity.stage],

    // Scores
    ['ICP Score', lead.intelligence.icpScore.toString()],
    ['Pain Score', lead.intelligence.painScore.toString()],
    ['Fit Score', lead.intelligence.fitScore.toString()],
    ['Strategy Score', lead.intelligence.strategyScore.toString()],
    ['Data Confidence', lead.intelligence.dataConfidence],

    // Metrics
    ['Revenue', lead.metrics.revenue],
    ['Volume', lead.metrics.volume],
    ['Estimated Lift', lead.metrics.estimatedLift],
    ['MIPS Score', lead.metrics.avgMipsScore?.toString() || 'N/A'],
    ['HPSA Designated', lead.metrics.isHpsa ? 'Yes' : 'No'],
    ['MUA Designated', lead.metrics.isMua ? 'Yes' : 'No'],

    // Intelligence
    ['Primary Driver', lead.signals.primaryDriver],
    ['Strategic Brief', `"${lead.intelligence.strategicBrief.replace(/"/g, '""')}"`],
  ];

  const csv = rows.map(row => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${clinic.name.replace(/[^a-z0-9]/gi, '_')}_lead_export.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copies lead data to clipboard (for quick paste into CRM)
 */
export async function copyLeadToClipboard(clinic: Clinic): Promise<void> {
  const lead = prepareLeadForExport(clinic);

  const text = `
🎯 LEAD EXPORT: ${lead.company.name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 OPPORTUNITY SUMMARY
• Deal: ${lead.opportunity.dealName}
• Value: ${lead.opportunity.estimatedValue} (${lead.opportunity.isVerified ? 'VERIFIED' : 'Projected'})
• Tier: ${lead.opportunity.tier}
• ICP Score: ${lead.intelligence.icpScore}/100
• Stage: ${lead.opportunity.stage}

🏥 ORGANIZATION INFO
• Name: ${lead.company.name}
• NPI: ${lead.company.npi}
• Phone: ${lead.company.phone}
• Address: ${lead.company.address}
• Segment: ${lead.company.segment}

📈 KEY METRICS
• Revenue: ${lead.metrics.revenue}
• Volume: ${lead.metrics.volume}
• MIPS Score: ${lead.metrics.avgMipsScore || 'N/A'}
• HPSA: ${lead.metrics.isHpsa ? 'Yes' : 'No'}
• MUA: ${lead.metrics.isMua ? 'Yes' : 'No'}

🎯 SCORING BREAKDOWN
• Pain: ${lead.intelligence.painScore}/40 pts
• Fit: ${lead.intelligence.fitScore}/30 pts
• Strategy: ${lead.intelligence.strategyScore}/30 pts
• Data Confidence: ${lead.intelligence.dataConfidence}%

💡 STRATEGIC INTELLIGENCE
${lead.intelligence.strategicBrief}

🔑 KEY SIGNALS
${lead.signals.keyDrivers.map(d => `• ${d.label}${d.value ? ': ' + d.value : ''}`).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated by Charta GTM Intelligence
  `.trim();

  await navigator.clipboard.writeText(text);
}
