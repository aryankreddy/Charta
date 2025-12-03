export interface Clinic {
  id: string;
  name: string;
  tier: string;
  score: number;
  segment: string;
  state: string;
  revenue: string;
  volume: string;
  volume_unit: string;  // "patients" or "encounters" - critical for accurate labeling
  est_revenue_lift: string;
  is_projected_lift: boolean;
  lift_basis: string;
  opportunity_breakdown?: {
    total: string;                 // Formatted total (e.g., "$2.5M")
    coding_lift: string;           // Formatted coding lift
    denial_prevention: string;     // Formatted denial prevention
    payer_mix_applied: boolean;    // True if FQHC discount applied
    winning_status: string;        // "WINNING" | "OPPORTUNITY" | "UNKNOWN"
  };
  billing_ratio: {
    level3: number;
    level4: number;
  };
  primary_driver: string;
  drivers: {
    label: string;
    value: string;
    color: string;
  }[];
  scoring_track: string;  // NEW: AMBULATORY, BEHAVIORAL, POST_ACUTE
  pain_label?: string;  // Dynamic pain driver label (e.g., "Undercoding Pain", "Margin Pressure")
  // The "Glass Box" Data
  analysis: {
    strategic_brief: string;  // Analyst report (not sales pitch)
    gaps: string[];
    benchmarks: {
      undercoding?: {
        value: number | null;
        national_avg: number;
        comparison: string;
        status: 'outperforming' | 'underperforming' | 'unknown';
      };
      psych_audit_risk?: {
        value: number;
        threshold: number;
        status: 'severe' | 'elevated' | 'normal';
        description: string;
      };
    };
    raw_scores: {
      pain: {
        total: number;
        signal: number;
        volume: number;
        margin: number;
        compliance: number;
      };
      fit: {
        total: number;
        alignment: number;
        complexity: number;
        chaos: number;
        risk: number;
      };
      strategy: {
        total: number;
        deal_size: number;
        expansion: number;
        referrals: number;
      };
      bonus: {
        strategic_scale: number;
      };
      base_before_bonus: number;
      final_score: number;
    };
    score_reasoning: {
      pain: string[];
      fit: string[];
      strategy: string[];
      bonus: string[];
    };
    data_confidence: string;
  };
  contact: {
    phone: string;
    email: string;
    address: string;
  };
  fit_reason: string;
  details: {
    raw: {
      undercoding_ratio: number | null;
      volume_source: string;
      volume_unit: string;  // "patients" or "encounters"
      revenue_source: string;
      avg_mips_score: number | null;
      mips_clinician_count: number | null;
      is_hpsa: boolean;
      is_mua: boolean;
      county_name: string | null;
    };
  };
}