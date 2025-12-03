# workers/enrich_duckdb.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

import duckdb


def mk_view_if_exists(
    con: duckdb.DuckDBPyConnection,
    name: str,
    path_str: str,
    select_sql: str,
    empty_cols: Iterable[Tuple[str, str]],
) -> None:
    """Create a DuckDB view when the parquet exists, otherwise an empty view."""

    path = Path(path_str) if path_str else None
    if path and path.exists():
        con.execute(f"CREATE OR REPLACE VIEW {name} AS {select_sql}")
        cnt = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"{name} -> {cnt} rows")
    else:
        cols_expr = ", ".join(
            f"CAST(NULL AS {dtype}) AS {col}" for col, dtype in empty_cols
        ) or "CAST(NULL AS VARCHAR) AS placeholder"
        empty_select = f"SELECT {cols_expr} WHERE 1=0"
        con.execute(f"CREATE OR REPLACE VIEW {name} AS {empty_select}")
        print(f"{name} -> 0 rows (missing: {path_str})")


BASE = Path(__file__).resolve().parents[1]
STAGING = BASE / "data" / "curated" / "staging"
OUT_CSV = BASE / "data" / "curated" / "clinics_scored.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

NPI = (STAGING / "stg_npi_orgs.parquet").as_posix()
PECOS = (STAGING / "stg_pecos_orgs.parquet").as_posix()
ACO = (STAGING / "stg_aco_orgs.parquet").as_posix()
UTIL = (STAGING / "stg_physician_util.parquet").as_posix()
HRSA = (STAGING / "stg_hrsa_sites.parquet").as_posix()

con = duckdb.connect()

mk_view_if_exists(
    con,
    "npi",
    NPI,
    f"SELECT * FROM read_parquet('{NPI}')",
    empty_cols=[
        ("npi", "VARCHAR"),
        ("org_name", "VARCHAR"),
        ("address", "VARCHAR"),
        ("city", "VARCHAR"),
        ("state", "VARCHAR"),
        ("zip", "VARCHAR"),
        ("phone", "VARCHAR"),
        ("tax1", "VARCHAR"),
        ("tax2", "VARCHAR"),
        ("tax3", "VARCHAR"),
    ],
)

mk_view_if_exists(
    con,
    "pecos",
    PECOS,
    f"SELECT * FROM read_parquet('{PECOS}')",
    empty_cols=[
        ("npi", "VARCHAR"),
        ("org_name", "VARCHAR"),
        ("state", "VARCHAR"),
        ("address", "VARCHAR"),
        ("specialties", "VARCHAR"),
    ],
)

mk_view_if_exists(
    con,
    "aco",
    ACO,
    f"SELECT * FROM read_parquet('{ACO}')",
    empty_cols=[
        ("participant_id", "VARCHAR"),
        ("org_name", "VARCHAR"),
        ("state", "VARCHAR"),
        ("aco_id", "VARCHAR"),
    ],
)

mk_view_if_exists(
    con,
    "util",
    UTIL,
    f"SELECT * FROM read_parquet('{UTIL}')",
    empty_cols=[
        ("npi", "VARCHAR"),
        ("services_count", "BIGINT"),
        ("allowed_amt", "DOUBLE"),
        ("bene_count", "BIGINT"),
    ],
)

mk_view_if_exists(
    con,
    "hrsa",
    HRSA,
    f"SELECT * FROM read_parquet('{HRSA}')",
    empty_cols=[
        ("site_id", "VARCHAR"),
        ("org_name", "VARCHAR"),
        ("site_name", "VARCHAR"),
        ("address", "VARCHAR"),
        ("city", "VARCHAR"),
        ("state", "VARCHAR"),
        ("zip", "VARCHAR"),
        ("fqhc_flag", "INT"),
    ],
)

final_select = """
WITH seg(prefix,label) AS (
  VALUES
    ('207Q','Primary Care'),
    ('207R','Primary Care'),
    ('208D','Primary Care'),
    ('363A','Primary Care'),
    ('363L','Primary Care'),
    ('261Q','Multi-specialty'),
    ('207RC','Cardiology'),
    ('207RE','Endocrinology'),
    ('207RG','Gastroenterology'),
    ('207V','OB/GYN'),
    ('207RX','Oncology'),
    ('207XX','Orthopedics')
),

tax_tokens AS (
  SELECT
    upper(coalesce(org_name,'')) AS org_name,
    upper(coalesce(state,''))    AS state,
    trim(tax)                    AS tax,
    substr(trim(tax),1,5)        AS tax5,
    substr(trim(tax),1,4)        AS tax4
  FROM (
    SELECT org_name, state, tax1 AS tax FROM npi
    UNION ALL
    SELECT org_name, state, tax2 AS tax FROM npi
    UNION ALL
    SELECT org_name, state, tax3 AS tax FROM npi
  ) AS src
  WHERE tax IS NOT NULL AND length(trim(tax)) >= 4
),

tax_seg AS (
  SELECT
    tt.org_name,
    tt.state,
    coalesce(s5.label, s4.label, 'Multi-specialty') AS segment_label
  FROM tax_tokens tt
  LEFT JOIN seg s5 ON tt.tax5 = s5.prefix
  LEFT JOIN seg s4 ON tt.tax4 = s4.prefix
),

org_segment AS (
  SELECT org_name, state, segment_label AS segment
  FROM (
    SELECT
      org_name,
      state,
      segment_label,
      cnt,
      row_number() OVER (
        PARTITION BY org_name, state
        ORDER BY cnt DESC, segment_label
      ) AS rn
  FROM (
    SELECT org_name, state, segment_label, count(*) AS cnt
    FROM tax_seg
    GROUP BY 1,2,3
    ) ranked
  )
  WHERE rn = 1
),

org_spine AS (
  SELECT
    trim(upper(coalesce(org_name,''))) AS org_norm,
    upper(coalesce(state,''))          AS state,
    max(coalesce(org_name,''))         AS org_name,
    max(coalesce(zip,''))              AS zip,
    count(*)                           AS npi_count,
    count(DISTINCT coalesce(city,'') || '-' || coalesce(zip,'')) AS site_count
  FROM npi
  GROUP BY 1,2
),

util_org AS (
  SELECT
    upper(n.org_name) AS org_name,
    upper(n.state)    AS state,
    sum(u.services_count)::DOUBLE AS services_count,
    sum(u.allowed_amt)::DOUBLE   AS allowed_amt,
    sum(u.bene_count)::DOUBLE    AS bene_count
  FROM npi n
  JOIN util u ON u.npi = n.npi
  GROUP BY 1,2
),

pecos_norm AS (
  SELECT DISTINCT trim(upper(org_name)) AS org_norm, upper(state) AS state
  FROM pecos
),

aco_norm AS (
  SELECT DISTINCT trim(upper(org_name)) AS org_norm, upper(state) AS state
  FROM aco
),

hrsa_norm AS (
  SELECT
    trim(upper(org_name)) AS org_norm,
    upper(state)          AS state,
    max(coalesce(fqhc_flag,0))      AS fqhc_flag
  FROM hrsa
  GROUP BY 1,2
),

joined AS (
  SELECT
    s.org_norm,
    s.org_name,
    s.state,
    s.zip,
    s.npi_count,
    s.site_count,
    coalesce(seg.segment, 'Multi-specialty') AS segment,
    CASE WHEN p.org_norm IS NOT NULL THEN 1 ELSE 0 END AS pecos_enrolled,
    CASE WHEN a.org_norm IS NOT NULL THEN 1 ELSE 0 END AS aco_member,
    coalesce(h.fqhc_flag, 0)                 AS fqhc_flag,
    coalesce(u.services_count,0)            AS services_count,
    coalesce(u.allowed_amt,0)               AS allowed_amt,
    coalesce(u.bene_count,0)                AS bene_count
  FROM org_spine s
  LEFT JOIN org_segment seg ON seg.org_name = s.org_norm AND seg.state = s.state
  LEFT JOIN pecos_norm p     ON p.org_norm   = s.org_norm AND p.state = s.state
  LEFT JOIN aco_norm a       ON a.org_norm   = s.org_norm AND a.state = s.state
  LEFT JOIN hrsa_norm h      ON h.org_norm   = s.org_norm AND h.state = s.state
  LEFT JOIN util_org u       ON u.org_name   = s.org_norm AND u.state = s.state
),

raw AS (
  SELECT
    *,
    CASE
      WHEN segment IN ('Primary Care','Multi-specialty','OB/GYN') THEN 10
      WHEN segment IN ('Cardiology','Endocrinology','Gastroenterology') THEN 7
      ELSE 4
    END AS segment_fit_raw,

    (ln(1+services_count) + 0.5*ln(1+coalesce(bene_count,0)) + 0.2*site_count) AS scale_velocity_raw,

    (2 + ln(1+site_count) + pecos_enrolled + aco_member) AS integration_ease_raw,

    coalesce((
      SELECT count(DISTINCT segment_label)
      FROM tax_seg t
      WHERE t.org_name = j.org_name AND t.state = j.state
    ), 1) AS coding_complexity_raw,

    coalesce((
      SELECT stddev_samp(CASE WHEN u2.bene_count>0 THEN u2.allowed_amt/u2.bene_count ELSE NULL END)
      FROM npi n2
      JOIN util u2 ON u2.npi = n2.npi
      WHERE upper(n2.org_name)=j.org_name AND upper(n2.state)=j.state
    ), 0) AS denial_pressure_raw,

    (aco_member + pecos_enrolled
     + CASE WHEN services_count>500 THEN 1 ELSE 0 END
     + CASE WHEN segment IN ('Primary Care','Multi-specialty') THEN 1 ELSE 0 END
     + CASE WHEN fqhc_flag > 0 THEN 1 ELSE 0 END) AS roi_readiness_raw
  FROM joined j
),

norm AS (
  SELECT
    *,
    CASE
      WHEN (min(segment_fit_raw) OVER () = max(segment_fit_raw) OVER ()) THEN 5.0
      ELSE (segment_fit_raw - min(segment_fit_raw) OVER ())
           / NULLIF(max(segment_fit_raw) OVER () - min(segment_fit_raw) OVER (),0) * 10
    END AS segment_fit,

    CASE
      WHEN (min(scale_velocity_raw) OVER () = max(scale_velocity_raw) OVER ()) THEN 5.0
      ELSE (scale_velocity_raw - min(scale_velocity_raw) OVER ())
           / NULLIF(max(scale_velocity_raw) OVER () - min(scale_velocity_raw) OVER (),0) * 10
    END AS scale_velocity,

    CASE
      WHEN (min(integration_ease_raw) OVER () = max(integration_ease_raw) OVER ()) THEN 5.0
      ELSE 10 - ((integration_ease_raw - min(integration_ease_raw) OVER ())
           / NULLIF(max(integration_ease_raw) OVER () - min(integration_ease_raw) OVER (),0) * 10)
    END AS emr_friction,

    CASE
      WHEN (min(coding_complexity_raw) OVER () = max(coding_complexity_raw) OVER ()) THEN 5.0
      ELSE (coding_complexity_raw - min(coding_complexity_raw) OVER ())
           / NULLIF(max(coding_complexity_raw) OVER () - min(coding_complexity_raw) OVER (),0) * 10
    END AS coding_complexity,

    CASE
      WHEN (min(denial_pressure_raw) OVER () = max(denial_pressure_raw) OVER ()) THEN 5.0
      ELSE (denial_pressure_raw - min(denial_pressure_raw) OVER ())
           / NULLIF(max(denial_pressure_raw) OVER () - min(denial_pressure_raw) OVER (),0) * 10
    END AS denial_pressure,

    CASE
      WHEN (min(roi_readiness_raw) OVER () = max(roi_readiness_raw) OVER ()) THEN 5.0
      ELSE (roi_readiness_raw - min(roi_readiness_raw) OVER ())
           / NULLIF(max(roi_readiness_raw) OVER () - min(roi_readiness_raw) OVER (),0) * 10
    END AS roi_readiness
  FROM raw
),

-- Check for primary care taxonomy codes
primary_care_check AS (
  SELECT DISTINCT
    tt.org_name,
    tt.state,
    1 AS has_primary_care_tax
  FROM tax_tokens tt
  WHERE tt.tax5 IN ('207Q', '207R') OR tt.tax4 = '2080' OR tt.tax LIKE '208000000X%'
),

scored_with_sector AS (
  SELECT
    n.*,
    CASE
      WHEN n.fqhc_flag = 1 THEN 'FQHC'
      WHEN pc.has_primary_care_tax = 1 THEN 'Primary Care'
      WHEN upper(coalesce(n.org_name, '')) LIKE '%HOSPITAL%'
        OR upper(coalesce(n.org_name, '')) LIKE '%MED CENTER%'
        OR upper(coalesce(n.org_name, '')) LIKE '%MEDICAL CENTER%'
        OR upper(coalesce(n.org_name, '')) LIKE '%HEALTH SYSTEM%'
        OR upper(coalesce(n.org_name, '')) LIKE '%HEALTHCARE SYSTEM%'
        THEN 'Health System / Hospital-affiliated'
      ELSE 'Specialty / Other'
    END AS sector
  FROM norm n
  LEFT JOIN primary_care_check pc ON pc.org_name = n.org_norm AND pc.state = n.state
),

-- Helper CTE to derive segment_label first (needed for segment-specific scoring)
segments_derived AS (
  SELECT
    s.*,
    -- Improved segment_label derivation using segment, sector, fqhc_flag, and org_name patterns
    CASE
      -- 1) FQHC / Community Health (highest priority)
      WHEN s.fqhc_flag = 1 THEN 'FQHC / Community Health'
      
      -- 2) Behavioral Health (check segment, sector, and org_name patterns)
      WHEN lower(coalesce(s.segment, '')) LIKE '%behavioral%'
        OR lower(coalesce(s.segment, '')) LIKE '%psychiat%'
        OR lower(coalesce(s.segment, '')) LIKE '%mental%'
        OR lower(coalesce(s.sector, '')) LIKE '%behavioral%'
        OR lower(coalesce(s.sector, '')) LIKE '%psychiat%'
        OR lower(coalesce(s.sector, '')) LIKE '%mental%'
        OR lower(coalesce(s.org_name, '')) LIKE '%behavior%'
        OR lower(coalesce(s.org_name, '')) LIKE '%psychiat%'
        OR lower(coalesce(s.org_name, '')) LIKE '%mental health%'
        OR lower(coalesce(s.org_name, '')) LIKE '%mentalhealth%'
        OR lower(coalesce(s.org_name, '')) LIKE '%psychology%'
        OR lower(coalesce(s.org_name, '')) LIKE '%counseling%'
        OR lower(coalesce(s.org_name, '')) LIKE '%therapy%'
        THEN 'Behavioral Health'
      
      -- 3) Home Health / Post-Acute (check segment, sector, and org_name patterns)
      WHEN lower(coalesce(s.segment, '')) LIKE '%home health%'
        OR lower(coalesce(s.segment, '')) LIKE '%hospice%'
        OR lower(coalesce(s.segment, '')) LIKE '%post-acute%'
        OR lower(coalesce(s.segment, '')) LIKE '%post acute%'
        OR lower(coalesce(s.sector, '')) LIKE '%home health%'
        OR lower(coalesce(s.sector, '')) LIKE '%hospice%'
        OR lower(coalesce(s.sector, '')) LIKE '%post-acute%'
        OR lower(coalesce(s.org_name, '')) LIKE '%home health%'
        OR lower(coalesce(s.org_name, '')) LIKE '%homehealth%'
        OR lower(coalesce(s.org_name, '')) LIKE '%hospice%'
        OR lower(coalesce(s.org_name, '')) LIKE '%visiting nurse%'
        OR lower(coalesce(s.org_name, '')) LIKE '%vna%'
        OR lower(coalesce(s.org_name, '')) LIKE '%skilled nursing%'
        OR lower(coalesce(s.org_name, '')) LIKE '%snf%'
        OR lower(coalesce(s.org_name, '')) LIKE '%post acute%'
        THEN 'Home Health / Post-Acute'
      
      -- 4) Multi-specialty / health system (check for health systems, networks, groups with multiple specialties)
      WHEN lower(coalesce(s.segment, '')) LIKE '%multi%'
        OR lower(coalesce(s.segment, '')) LIKE '%system%'
        OR lower(coalesce(s.segment, '')) LIKE '%network%'
        OR s.segment = 'Multi-specialty'
        OR lower(coalesce(s.sector, '')) LIKE '%health system%'
        OR lower(coalesce(s.sector, '')) LIKE '%hospital%'
        OR lower(coalesce(s.org_name, '')) LIKE '%health system%'
        OR lower(coalesce(s.org_name, '')) LIKE '%healthsystem%'
        OR lower(coalesce(s.org_name, '')) LIKE '%health care system%'
        OR lower(coalesce(s.org_name, '')) LIKE '%medical group%'
        OR lower(coalesce(s.org_name, '')) LIKE '%physician group%'
        OR lower(coalesce(s.org_name, '')) LIKE '%medical center%'
        OR (s.site_count > 5 AND s.npi_count > 10)  -- Large multi-site organizations
        THEN 'Multi-specialty'
      
      -- 5) Primary Care (check segment, sector, taxonomy, and org_name patterns)
      WHEN lower(coalesce(s.segment, '')) LIKE '%primary care%'
        OR lower(coalesce(s.segment, '')) LIKE '%family medicine%'
        OR lower(coalesce(s.segment, '')) LIKE '%internal medicine%'
        OR s.segment = 'Primary Care'
        OR lower(coalesce(s.sector, '')) LIKE '%primary care%'
        OR lower(coalesce(s.sector, '')) LIKE '%family medicine%'
        OR pc.has_primary_care_tax = 1
        OR lower(coalesce(s.org_name, '')) LIKE '%family practice%'
        OR lower(coalesce(s.org_name, '')) LIKE '%family medicine%'
        OR lower(coalesce(s.org_name, '')) LIKE '%primary care%'
        OR lower(coalesce(s.org_name, '')) LIKE '%internal medicine%'
        OR lower(coalesce(s.org_name, '')) LIKE '%pediatrics%'
        OR lower(coalesce(s.org_name, '')) LIKE '%pediatric%'
        THEN 'Primary Care'
      
      -- Fallback to "Other"
      ELSE 'Other'
    END AS segment_label
  FROM scored_with_sector s
  LEFT JOIN primary_care_check pc ON pc.org_name = s.org_norm AND pc.state = s.state
),

-- Calculate care_intensity once for reuse
care_intensity_calc AS (
  SELECT
    sd.*,
    -- Care intensity proxy: log10(allowed_amt / bene_count + 1) scaled to 0-10
    LEAST(10.0, GREATEST(0.0,
      CASE
        WHEN COALESCE(sd.bene_count, 0) > 0 
          THEN LN(1.0 + (COALESCE(sd.allowed_amt, 0.0) / sd.bene_count)) / LN(10.0) * 2.5
        ELSE 0.0
      END
    )) AS care_intensity
  FROM segments_derived sd
),

gtm_intelligence AS (
  SELECT
    cic.*,
    -- Segment-specific structural_fit_score calculation
    CASE
      WHEN cic.segment_label = 'FQHC / Community Health' THEN
        -- FQHCs: compliance + primary care fit
        LEAST(10.0, GREATEST(0.0,
          0.40 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.segment_fit, 0.0))) +
          0.25 * GREATEST(0.0, LEAST(10.0, COALESCE(10.0 - cic.emr_friction, 0.0))) +
          0.20 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.coding_complexity, 0.0))) +
          0.15 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.scale_velocity, 0.0)))
        ))
      WHEN cic.segment_label IN ('Behavioral Health', 'Home Health / Post-Acute') THEN
        -- Documentation-heavy, complex coding
        LEAST(10.0, GREATEST(0.0,
          0.30 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.segment_fit, 0.0))) +
          0.35 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.coding_complexity, 0.0))) +
          0.20 * GREATEST(0.0, LEAST(10.0, COALESCE(10.0 - cic.emr_friction, 0.0))) +
          0.15 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.scale_velocity, 0.0)))
        ))
      WHEN cic.segment_label = 'Multi-specialty' THEN
        -- Roll-ups / platforms: scale + fit
        LEAST(10.0, GREATEST(0.0,
          0.35 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.segment_fit, 0.0))) +
          0.30 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.scale_velocity, 0.0))) +
          0.20 * GREATEST(0.0, LEAST(10.0, COALESCE(10.0 - cic.emr_friction, 0.0))) +
          0.15 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.coding_complexity, 0.0)))
        ))
      ELSE
        -- Primary care / Other: default weighting
        LEAST(10.0, GREATEST(0.0,
          0.35 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.segment_fit, 0.0))) +
          0.25 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.coding_complexity, 0.0))) +
          0.20 * GREATEST(0.0, LEAST(10.0, COALESCE(10.0 - cic.emr_friction, 0.0))) +
          0.20 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.scale_velocity, 0.0)))
        ))
    END AS structural_fit_score,
    
    -- Segment-specific propensity_score calculation
    CASE
      WHEN cic.segment_label IN ('Behavioral Health', 'Home Health / Post-Acute') THEN
        LEAST(10.0, GREATEST(0.0,
          0.40 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.denial_pressure, 0.0))) +
          0.25 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.roi_readiness, 0.0))) +
          0.20 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.coding_complexity, 0.0))) +
          0.15 * cic.care_intensity
        ))
      WHEN cic.segment_label = 'FQHC / Community Health' THEN
        LEAST(10.0, GREATEST(0.0,
          0.35 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.denial_pressure, 0.0))) +
          0.30 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.roi_readiness, 0.0))) +
          0.20 * cic.care_intensity +
          0.15 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.scale_velocity, 0.0)))
        ))
      WHEN cic.segment_label = 'Multi-specialty' THEN
        LEAST(10.0, GREATEST(0.0,
          0.30 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.denial_pressure, 0.0))) +
          0.30 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.roi_readiness, 0.0))) +
          0.25 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.scale_velocity, 0.0))) +
          0.15 * cic.care_intensity
        ))
      ELSE
        -- Primary care / Other: default weighting
        LEAST(10.0, GREATEST(0.0,
          0.35 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.denial_pressure, 0.0))) +
          0.30 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.roi_readiness, 0.0))) +
          0.20 * cic.care_intensity +
          0.15 * GREATEST(0.0, LEAST(10.0, COALESCE(cic.scale_velocity, 0.0)))
        ))
    END AS propensity_score
  FROM care_intensity_calc cic
),

-- Calculate primary_driver based on highest-scoring driver
driver_scores AS (
  SELECT
    g.*,
    GREATEST(0.0, LEAST(10.0, COALESCE(g.denial_pressure, 0.0))) AS denial_pressure_norm,
    GREATEST(0.0, LEAST(10.0, COALESCE(g.roi_readiness, 0.0))) AS roi_readiness_norm,
    GREATEST(0.0, LEAST(10.0, COALESCE(g.scale_velocity, 0.0))) AS scale_velocity_norm,
    GREATEST(0.0, LEAST(10.0, COALESCE(10.0 - g.emr_friction, 0.0))) AS integration_ease_norm,
    GREATEST(0.0, LEAST(10.0, COALESCE(g.coding_complexity, 0.0))) AS coding_complexity_norm,
    -- Combine ROI + care_intensity for "Revenue lift" driver
    GREATEST(0.0, LEAST(10.0, 
      (GREATEST(0.0, LEAST(10.0, COALESCE(g.roi_readiness, 0.0))) * 0.6 +
       g.care_intensity * 0.4)
    )) AS revenue_lift_score
  FROM gtm_intelligence g
),

final_scored AS (
  SELECT
    ds.*,
    -- Updated icf_tier thresholds: 1=high fit+urgency, 2=decent, 3=everyone else
    CASE
      WHEN ds.structural_fit_score >= 7.5 AND ds.propensity_score >= 7.0 THEN 1
      WHEN ds.structural_fit_score >= 6.0 AND ds.propensity_score >= 5.5 THEN 2
      ELSE 3
    END AS icf_tier,
    -- Improved primary_driver: map to GTM-friendly themes
    CASE
      WHEN ds.denial_pressure_norm >= GREATEST(
        ds.revenue_lift_score,
        ds.scale_velocity_norm,
        ds.integration_ease_norm,
        ds.coding_complexity_norm
      ) THEN 'Denial pressure'
      WHEN ds.revenue_lift_score >= GREATEST(
        ds.scale_velocity_norm,
        ds.integration_ease_norm,
        ds.coding_complexity_norm
      ) THEN 'Revenue lift'
      WHEN ds.scale_velocity_norm >= GREATEST(
        ds.integration_ease_norm,
        ds.coding_complexity_norm
      ) THEN 'Scale & velocity'
      WHEN ds.integration_ease_norm >= ds.coding_complexity_norm
        THEN 'Integration ease'
      ELSE 'Coding complexity'
    END AS primary_driver
  FROM driver_scores ds
)

SELECT
  COALESCE(
    NULLIF(
      lower(replace(regexp_replace(org_name,'[^A-Z0-9]+','-','g'), '--','-')) || '-' || state,
      '-'
    ),
    md5(coalesce(org_name,'') || '-' || coalesce(state,''))
  ) AS clinic_id,
  COALESCE(org_name, 'Unknown')             AS account_name,
  COALESCE(state, 'NA')                     AS state_code,
  COALESCE(segment, 'Multi-specialty')      AS segment,
  COALESCE(sector, 'Specialty / Other')     AS sector,
  COALESCE(segment_label, 'Other')          AS segment_label,
  ROUND(
      0.25*segment_fit +
      0.20*scale_velocity +
      0.15*emr_friction +
      0.15*coding_complexity +
      0.15*denial_pressure +
      0.10*roi_readiness
    , 1) AS icf_score,
  ROUND(structural_fit_score, 1)            AS structural_fit_score,
  ROUND(propensity_score, 1)                 AS propensity_score,
  icf_tier,
  primary_driver,
  ROUND(segment_fit,1)       AS segment_fit,
  ROUND(scale_velocity,1)    AS scale_velocity,
  ROUND(emr_friction,1)      AS emr_friction,
  ROUND(coding_complexity,1) AS coding_complexity,
  ROUND(denial_pressure,1)   AS denial_pressure,
  ROUND(roi_readiness,1)     AS roi_readiness,
  aco_member,
  pecos_enrolled,
  fqhc_flag,
  site_count,
  npi_count,
  services_count,
  bene_count,
  allowed_amt
FROM final_scored
WHERE COALESCE(org_name, '') <> ''
ORDER BY icf_score DESC, account_name ASC
"""

con.execute(f"COPY ({final_select}) TO '{OUT_CSV.as_posix()}' (HEADER, DELIMITER ',');")

rows = con.execute(
    f"SELECT COUNT(*) FROM read_csv_auto('{OUT_CSV.as_posix()}')"
).fetchone()[0]
distinct_icf = con.execute(
    f"SELECT COUNT(DISTINCT icf_score) FROM read_csv_auto('{OUT_CSV.as_posix()}')"
).fetchone()[0]
print("clinics_scored.csv →", rows, "rows; distinct ICF:", distinct_icf)
preview = con.execute(
    f"SELECT account_name,state_code,segment_label,structural_fit_score,propensity_score,icf_tier,primary_driver FROM read_csv_auto('{OUT_CSV.as_posix()}') LIMIT 10"
).fetchall()
print("\nPreview (GTM fields):")
for row in preview:
    print(f"  {row[0][:40]:<40} | {row[1]:<3} | {row[2]:<25} | Fit:{row[3]:.1f} | Prop:{row[4]:.1f} | Tier:{row[5]} | {row[6]}")
