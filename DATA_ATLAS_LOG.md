# CHARTA HEALTH DATA ATLAS
**Generated:** 2025-11-21 20:23:57.321123

> This document lists every data file available to the scoring engine, enabling us to identify 'Dark Matter' data assets.


### 📂 //

- **📄 Data_Explorer_Dataset (1).csv** (2.13 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7

## 📂 /staging

- **📄 oig_leie_raw.csv** (14.58 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, address, city, state, zip, reindate, wvrstate`
  - 📋 **Cols:** LASTNAME, FIRSTNAME, MIDNAME, BUSNAME, GENERAL, SPECIALTY, UPIN, NPI, DOB, ADDRESS, ... (+8 more)

## 📂 /raw

### 📂 /raw/physician_utilization

#### 📂 /raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service

##### 📂 /raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023

- **📄 MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv** (2920.47 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `rndrng_npi, rndrng_prvdr_city, rndrng_prvdr_state_abrvtn, rndrng_prvdr_state_fips, rndrng_prvdr_zip5`
  - 📋 **Cols:** Rndrng_NPI, Rndrng_Prvdr_Last_Org_Name, Rndrng_Prvdr_First_Name, Rndrng_Prvdr_MI, Rndrng_Prvdr_Crdntls, Rndrng_Prvdr_Ent_Cd, Rndrng_Prvdr_St1, Rndrng_Prvdr_St2, Rndrng_Prvdr_City, Rndrng_Prvdr_State_Abrvtn, ... (+18 more)

- **📄 MUP_PHY_RY25_20250408_TBL_POS.xlsx** (0.01 MB)
  - ⚠️ **Error:** Missing optional dependency 'openpyxl'.  Use pip or conda to install openpyxl.

### 📂 /raw/aco

#### 📂 /raw/aco/Accountable Care Organizations

##### 📂 /raw/aco/Accountable Care Organizations/2025

- **📄 PY2025_PC_Flex_ACO.csv** (0.01 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `aco_address`
  - 💰 **VALUE:** `high_revenue_aco, low_revenue_aco, aco_exec_email, aco_exec_phone, aco_public_email, aco_public_phone`
  - 📋 **Cols:** aco_id, aco_name, aco_service_area, agreement_period_num, initial_start_date, current_start_date, re-entering_aco, basic_track, basic_track_level, enhanced_track, ... (+20 more)

- **📄 py2025_medicare_shared_savings_program_organizations.csv** (0.17 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `aco_address`
  - 💰 **VALUE:** `high_revenue_aco, low_revenue_aco, aco_exec_email, aco_exec_phone, aco_public_email, aco_public_phone`
  - 📋 **Cols:** aco_id, aco_name, aco_service_area, agreement_period_num, initial_start_date, current_start_date, re-entering_aco, basic_track, basic_track_level, enhanced_track, ... (+21 more)

### 📂 /raw/npi_registry

### 📂 /raw/cost_reports_fqhc

#### 📂 /raw/cost_reports_fqhc/FQHC14-REPORTS

#### 📂 /raw/cost_reports_fqhc/FQHC14-ALL-YEARS (1)

- **📄 FQHC14_2014_alpha.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 4605, S000001, 00400, 00100, N

- **📄 FQHC14_2014_nmrc.csv** (0.00 MB)
  - ⚠️ **Error:** No columns to parse from file

- **📄 FQHC14_2014_rpt.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 4605, 1, 251015, Unnamed: 3, 2, 07/01/2014, 01/31/2015, 06/30/2017, N, N.1, ... (+8 more)

- **📄 FQHC14_2015_alpha.csv** (14.36 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 88, S000001, 00100, 00100.1, X

- **📄 FQHC14_2015_nmrc.csv** (17.02 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 168, A000000, 00100, 00200, 454161

- **📄 FQHC14_2015_rpt.csv** (0.21 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 88, 4, 511067, Unnamed: 3, 2, 01/28/2015, 02/28/2015, 07/27/2016, Y, N, ... (+8 more)

- **📄 FQHC14_2016_alpha.csv** (16.16 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 361, S000001, 00400, 00100, N

- **📄 FQHC14_2016_nmrc.csv** (19.18 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 1309, A000000, 00300, 00200, 14086

- **📄 FQHC14_2016_rpt.csv** (0.25 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 361, 4, 511085, Unnamed: 3, 2, 10/26/2015, 02/29/2016, 09/30/2016, Y, N, ... (+8 more)

- **📄 FQHC14_2017_alpha.csv** (17.50 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 3734, S000001, 00400, 00100, L

- **📄 FQHC14_2017_nmrc.csv** (20.49 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 3881, A000000, 00100, 00200, 274640

- **📄 FQHC14_2017_rpt.csv** (0.26 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 3734, 4, 181987, Unnamed: 3, 2, 10/28/2016, 12/31/2016, 04/27/2017, N, N.1, ... (+8 more)

- **📄 FQHC14_2018_alpha.csv** (18.14 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 9447, S000001, 00400, 00100, N

- **📄 FQHC14_2018_nmrc.csv** (21.20 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 9817, A000000, 00100, 00200, 9877

- **📄 FQHC14_2018_rpt.csv** (0.27 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 9447, 5, 181038, Unnamed: 3, 2, 11/06/2017, 12/31/2017, 06/27/2018, N, N.1, ... (+8 more)

- **📄 FQHC14_2019_alpha.csv** (19.18 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 13784, S000001, 00400, 00100, N

- **📄 FQHC14_2019_nmrc.csv** (22.45 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 14865, A000000, 00100, 00200, 180196

- **📄 FQHC14_2019_rpt.csv** (0.30 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 13784, 1, 061987, Unnamed: 3, 2, 11/12/2018, 12/31/2018, 05/10/2019, N, N.1, ... (+8 more)

- **📄 FQHC14_2020_alpha.csv** (19.73 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 18534, S000001, 00400, 00100, L

- **📄 FQHC14_2020_nmrc.csv** (22.49 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 18537, A000000, 00100, 00200, 294565

- **📄 FQHC14_2020_rpt.csv** (0.31 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 18534, 3, 941055, Unnamed: 3, 2, 11/01/2019, 12/31/2019, 05/14/2020, Y, N, ... (+8 more)

- **📄 FQHC14_2021_alpha.csv** (20.16 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 23890, S000001, 00400, 00100, N

- **📄 FQHC14_2021_nmrc.csv** (22.97 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 25247, A000000, 00200, 00600, 8345

- **📄 FQHC14_2021_rpt.csv** (0.29 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 23890, 2, 231020, Unnamed: 3, 2.1, 10/01/2020, 12/08/2020, 06/10/2021, N, Y, ... (+8 more)

- **📄 FQHC14_2022_alpha.csv** (20.96 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 28712, S000001, 00400, 00100, N

- **📄 FQHC14_2022_nmrc.csv** (23.59 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 29610, A000000, 00100, 00200, 2540

- **📄 FQHC14_2022_rpt.csv** (0.30 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 28712, 4, 491982, Unnamed: 3, 2, 10/19/2021, 12/31/2021, 04/26/2022, N, N.1, ... (+8 more)

- **📄 FQHC14_2023_alpha.csv** (21.57 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 33844, S000001, 00400, 00100, L

- **📄 FQHC14_2023_nmrc.csv** (23.78 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 35355, A000000, 00400, 00200, 828

- **📄 FQHC14_2023_rpt.csv** (0.32 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 33844, 1, 851176, Unnamed: 3, 2, 10/01/2022, 12/31/2022, 05/26/2023, N, N.1, ... (+8 more)

- **📄 FQHC14_2024_alpha.csv** (9.28 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 39211, S000001, 00400, 00100, N

- **📄 FQHC14_2024_nmrc.csv** (10.35 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 39909, A000000, 00100, 00200, 36689

- **📄 FQHC14_2024_rpt.csv** (0.13 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 39211, 2, 371011, Unnamed: 3, 2.1, 10/23/2023, 11/30/2023, 05/13/2024, Y, N, ... (+8 more)

- **📄 FQHC14_2025_alpha.csv** (0.04 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 46260, S000001, 00400, 00100, N

- **📄 FQHC14_2025_nmrc.csv** (0.04 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 46407, A000000, 00100, 00200, 120461

- **📄 FQHC14_2025_rpt.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** 46260, Unnamed: 1, C51073, Unnamed: 3, 2, 11/15/2024, 12/31/2024, 04/24/2025, Y, N, ... (+8 more)

#### 📂 /raw/cost_reports_fqhc/FQHC14-DOCUMENTATION

- **📄 FQHC14_README.txt** (0.01 MB)

- **📄 HCRIS_DataDictionary.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** Column Code, TABLES, SUBSYSTEM, Null/Not Null, Title, Description, Valid Entries

- **📄 HCRIS_FACILITY_NUMBERING.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** From, To, Type of Facility

- **📄 HCRIS_STATE_CODES.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `state_name, ssa_state_cd`
  - 📋 **Cols:** State_Name, Ssa_State_Cd

- **📄 HCRIS_TABLE_DESCRIPTIONS _AND_SQL.txt** (0.00 MB)

### 📂 /raw/cost_reports_hospitals

#### 📂 /raw/cost_reports_hospitals/HOSPITAL2010-DOCUMENTATION

- **📄 HCRIS_DataDictionary.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** Column Code, TABLES, SUBSYSTEM, Null/Not Null, Title, Description, Valid Entries

- **📄 HCRIS_FACILITY_NUMBERING.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** From, To, Type of Facility

- **📄 HCRIS_STATE_CODES.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `state_name, ssa_state_cd`
  - 📋 **Cols:** State_Name, Ssa_State_Cd

- **📄 HCRIS_TABLE_DESCRIPTIONS _AND_SQL.txt** (0.00 MB)

- **📄 HOSP2010_CROSSWALK.xlsx** (0.21 MB)
  - ⚠️ **Error:** Missing optional dependency 'openpyxl'.  Use pip or conda to install openpyxl.

- **📄 HOSP2010_README.txt** (0.01 MB)

#### 📂 /raw/cost_reports_hospitals/HOSP10-REPORTS 2

### 📂 /raw/hrsa

- **📄 Health_Center_Service_Delivery_and_LookAlike_Sites (1).csv** (2.13 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7

### 📂 /raw/pecos

#### 📂 /raw/pecos/Medicare Fee-For-Service  Public Provider Enrollment

##### 📂 /raw/pecos/Medicare Fee-For-Service  Public Provider Enrollment/2025-Q3

- **📄 PPEF_Additional_NPIs_2025.10.01.csv** (2.97 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi`
  - 📋 **Cols:** ENRLMT_ID, NPI

- **📄 PPEF_Enrollment_Extract_2025.10.01.csv** (301.57 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, multiple_npi_flag, provider_type_cd, provider_type_desc, state_cd`
  - 📋 **Cols:** NPI, MULTIPLE_NPI_FLAG, PECOS_ASCT_CNTL_ID, ENRLMT_ID, PROVIDER_TYPE_CD, PROVIDER_TYPE_DESC, STATE_CD, FIRST_NAME, MDL_NAME, LAST_NAME, ... (+1 more)

- **📄 PPEF_Practice_Location_Extract_2025.10.01.csv** (40.66 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `city_name, state_cd, zip_cd`
  - 📋 **Cols:** ENRLMT_ID, CITY_NAME, STATE_CD, ZIP_CD

- **📄 PPEF_Reassignment_Extract_2025.10.01.csv** (107.49 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** REASGN_BNFT_ENRLMT_ID, RCV_BNFT_ENRLMT_ID

- **📄 PPEF_Secondary_Specialty_Extract_2025.10.01.csv** (27.09 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `provider_type_cd, provider_type_desc`
  - 📋 **Cols:** ENRLMT_ID, PROVIDER_TYPE_CD, PROVIDER_TYPE_DESC

### 📂 /raw/cost_reports_hha

#### 📂 /raw/cost_reports_hha/HHA20-REPORTS (1)

#### 📂 /raw/cost_reports_hha/HHA20-DOCUMENTATION

- **📄 HCRIS_DataDictionary.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** Column Code, TABLES, SUBSYSTEM, Null/Not Null, Title, Description, Valid Entries

- **📄 HCRIS_TABLE_DESCRIPTIONS _AND_SQL.txt** (0.00 MB)

- **📄 HHA20_README.txt** (0.01 MB)

## 📂 /curated

- **📄 clinics_enriched_scored.csv** (397.64 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, state_code, scale_velocity, npi_count`
  - 💰 **VALUE:** `real_annual_encounters, real_medicare_revenue, fqhc_revenue, fqhc_margin, icp_score, final_revenue, revenue_source, margin_source, score_p1_margin, score_p1_volume, score_p1_leakage, score_p2_align, score_p2_complex, score_p2_tech, score_p2_risk, score_p3_deal, score_p3_expand, score_p3_ref`
  - 📋 **Cols:** clinic_id, npi, org_name, state_code, taxonomy, segment_label, site_count, fqhc_flag, aco_member, segment_fit, ... (+38 more)

- **📄 clinics_icp.csv** (584.03 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, state_code, scale_velocity, npi_count, state_multiplier, estimated_capacity`
  - 💰 **VALUE:** `score_burnout, score_leakage, score_fit, score_propensity, icp_total_score, network_score`
  - 📋 **Cols:** clinic_id, npi, org_name, state_code, taxonomy, segment_label, site_count, fqhc_flag, aco_member, segment_fit, ... (+30 more)

- **📄 clinics_icp_with_networks.csv** (136.38 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `state_code`
  - 💰 **VALUE:** `icp_total_score, icp_fit_score, icp_pain_score, icp_compliance_score, icp_propensity_score, icp_scale_score, icp_segment_score, network_icp_score`
  - 📋 **Cols:** clinic_id, state_code, icp_total_score, icp_tier, icp_tier_label, icp_segment, icp_fit_score, icp_pain_score, icp_compliance_score, icp_propensity_score, ... (+11 more)

- **📄 clinics_scored.csv** (354.21 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, state_code, scale_velocity, npi_count`
  - 💰 **VALUE:** `icp_score, score_p1_margin, score_p1_volume, score_p1_leakage, score_p2_align, score_p2_complex, score_p2_tech, score_p2_risk, score_p3_deal, score_p3_expand, score_p3_ref, est_annual_revenue, est_annual_encounters`
  - 📋 **Cols:** clinic_id, npi, org_name, state_code, taxonomy, segment_label, site_count, fqhc_flag, aco_member, segment_fit, ... (+29 more)

- **📄 clinics_seed.csv** (213.80 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, state_code, scale_velocity, npi_count`
  - 📋 **Cols:** clinic_id, npi, org_name, state_code, taxonomy, segment_label, site_count, fqhc_flag, aco_member, segment_fit, ... (+12 more)

- **📄 clinics_segmented_v2.csv** (1936.20 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, state_code, address, city, scale_velocity, npi_count`
  - 💰 **VALUE:** `structural_fit_score, propensity_score, icf_score, icp_fit_score, icp_pain_score, icp_compliance_score, icp_propensity_score, icp_scale_score, icp_segment_score, icp_total_score, network_icp_score`
  - 📋 **Cols:** clinic_id, npi, org_name, state_code, address, city, site_count, fqhc_flag, aco_member, org_like, ... (+51 more)

- **📄 icp_scores.csv** (1604.52 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `state_code`
  - 💰 **VALUE:** `icp_total_score, icp_fit_score, icp_pain_score, icp_compliance_score, icp_propensity_score, icp_scale_score, icp_segment_score`
  - 📋 **Cols:** clinic_id, state_code, icp_total_score, icp_tier, icp_tier_label, icp_segment, icp_fit_score, icp_pain_score, icp_compliance_score, icp_propensity_score, ... (+6 more)

- **📄 networks_icp.csv** (4.24 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi_count`
  - 💰 **VALUE:** `network_score`
  - 📋 **Cols:** network_id, network_name, num_clinics, network_score, npi_count, allowed_amt

- **📄 scores_seed.csv** (224.41 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 💰 **VALUE:** `structural_fit_score, propensity_score, icf_score`
  - 📋 **Cols:** clinic_id, structural_fit_score, propensity_score, icf_score, tier, icf_tier, primary_pain_driver, primary_driver, fit_chart_volume_complexity, fit_billing_model_fit, ... (+8 more)

### 📂 /curated/staging

- **📄 data_inventory_by_segment.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** segment, count, services_count_available, allowed_amt_available, fqhc_flag, aco_member, pecos_enrolled

- **📄 extraction_log.txt** (0.00 MB)

- **📄 fqhc_enriched_2024.csv** (0.05 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 💰 **VALUE:** `total_revenue, net_margin, medicare_revenue, medicaid_revenue, other_revenue`
  - 📋 **Cols:** RPT_REC_NUM, PRVDR_NUM, total_revenue, total_expenses, net_margin, medicare_revenue, medicaid_revenue, other_revenue, medicare_pct, medicaid_pct, ... (+1 more)

- **📄 fqhc_nmrc_2024_pivoted.csv** (0.71 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** RPT_REC_NUM, 100, 101, 102, 103, 104, 105, 106, 107, 108, ... (+457 more)

- **📄 fqhc_rpt_2024_debug.csv** (0.13 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 📋 **Cols:** RPT_REC_NUM, col1, PRVDR_NUM, col3, col4, col5, col6, col7, col8, col9, ... (+8 more)

- **📄 oig_leie_matches.csv** (0.05 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `npi, leie_npi`
  - 📋 **Cols:** clinic_id, npi, clinic_name, leie_business_name, exclusion_date, exclusion_type, match_type, match_confidence, leie_npi

- **📄 stg_aco_orgs.parquet** (0.02 MB)
  - 📊 **Rows:** 24
  - 🔗 **KEYS:** `aco_address`
  - 💰 **VALUE:** `high_revenue_aco, low_revenue_aco, aco_exec_email, aco_exec_phone, aco_public_email, aco_public_phone`
  - 📋 **Cols:** aco_id, aco_name, aco_service_area, agreement_period_num, initial_start_date, current_start_date, re-entering_aco, basic_track, basic_track_level, enhanced_track, ... (+20 more)

- **📄 stg_hcris_fqhc.csv** (0.00 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `provider_num`
  - 📋 **Cols:** provider_num, facility_type

- **📄 stg_hcris_fqhc.parquet** (0.00 MB)
  - 📊 **Rows:** 101
  - 🔗 **KEYS:** `provider_num`
  - 📋 **Cols:** provider_num, facility_type

- **📄 stg_hcris_hha.parquet** (0.00 MB)
  - 📊 **Rows:** 0
  - 📋 **Cols:** 

- **📄 stg_hcris_hospital.parquet** (0.00 MB)
  - 📊 **Rows:** 0
  - 📋 **Cols:** 

- **📄 stg_hcris_rhc.parquet** (0.00 MB)
  - 📊 **Rows:** 0
  - 📋 **Cols:** 

- **📄 stg_hrsa_sites.csv** (0.26 MB)
  - 📊 **Rows:** Unknown (CSV)
  - 🔗 **KEYS:** `address, city, state, zip, npi`
  - 📋 **Cols:** site_id, org_name, site_name, address, city, state, zip, npi, fqhc_flag

- **📄 stg_hrsa_sites.parquet** (0.12 MB)
  - 📊 **Rows:** 18657
  - 🔗 **KEYS:** `address, city, state, zip, npi`
  - 📋 **Cols:** site_id, org_name, site_name, address, city, state, zip, npi, fqhc_flag

- **📄 stg_npi_orgs.parquet** (67.47 MB)
  - 📊 **Rows:** 1867280
  - 🔗 **KEYS:** `npi, address, city, state, zip`
  - 💰 **VALUE:** `phone`
  - 📋 **Cols:** npi, org_name, address, city, state, zip, phone, taxonomy

- **📄 stg_pecos_orgs.parquet** (21.86 MB)
  - 📊 **Rows:** 2521536
  - 🔗 **KEYS:** `npi, state`
  - 📋 **Cols:** npi, org_name, state

- **📄 stg_physician_util.parquet** (20.09 MB)
  - 📊 **Rows:** 1175281
  - 🔗 **KEYS:** `npi`
  - 📋 **Cols:** npi, services_count, allowed_amt, bene_count
