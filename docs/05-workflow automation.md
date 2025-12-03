# 05_Workflow_Automation.md — Outbound-Ready Automation & GTM Playbook

> Purpose: define how to turn the scored clinic dataset into **actionable GTM assets** for Charta Health: export lists, narrative templates, campaign segments, and feedback loops.

---

## 0) High-Level Workflow

1. Filter high-fit clinics using dashboard or script (`icf_score ≥ threshold`).
2. Export into CRM-ready format (CSV) with key fields + narrative snippet.
3. Generate personalized outreach messaging (email/LinkedIn) using template + clinic data.
4. Feed responses back into system (update field: `contacted_at`, `status`, `outcome`).
5. Iterate scoring model with feedback (won/lost signals) → refine for next wave.

---

## 1) Export Format (CSV)

**Columns**:

* account_name
* brand_name
* state_code
* segments (pipe-delimited)
* num_locations
* num_clinicians_proxy
* emr_vendor
* icf_score
* top_drivers (pipe-delimited “driver: reason”)
* narrative_snippet
* website
* phone
* note (optional)

**Example row**:

```
Family Care Center, Family Care Center, TX, behavioral_health|primary_care, 5, 42, athenahealth, 91, denial_pressure: “state prior=high + denial roles”, emr_friction: “common EMR”, coding_complexity: “multi-service & coder hiring”, “We identified a 5-site behavioral health practice likely facing documentation and coding leakage under athenahealth. With 5+ locations and active coder hiring, an ~11% RVU uplift is realistic for you.”, https://familycaretx.com, 512-555-1234, 
```

---

## 2) Narrative Snippet Template

**Template**:

> Hi [FirstName],
>
> I came across **[BrandName]** based in **[State]**, with **[NumLocations]** locations and using **[EMRVendor]**. Given your segment in **[Segment]** and your scale, our data suggests you may be sitting on a ~**11 %+ RVU uplift** opportunity—as well as elevated documentation & denial risk centered around **[TopDriver1Reason]**.
>
> I lead GTM at Charta Health and we’ve helped clinics like yours automate 100 % of pre-bill reviews, avoid denials, and increase per-visit revenue by up to 15.2 %.
>
> Can we schedule 15 minutes next week to walk through what your peers are doing and map a tailored opportunity for you?
>
> Best,
> [YourName]

**Implementation**:

* Placeholders filled from export row.
* TopDriver1Reason pulled from `top_drivers` field.
* Variation engine: rotate first sentence, bold key metric (11% → actual modelled for that clinic).
* Store in `outbound_templates` table for reuse.

---

## 3) Segment Playbooks

**Segment playbooks** tailor message and filters:

| Segment           | Filter Criteria                                                | Messaging Focus                                            |
| ----------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| Primary Care      | `segments includes primary_care` + `icf_score ≥ 75`            | “Under-billing, RVU capture, simple EMR stack”             |
| Behavioral Health | `segments includes behavioral_health` + `denial_pressure ≥ 10` | “Denial risk from payer scrutiny, documentation gap”       |
| Home Health       | `segments includes home_health` + `num_locations ≥ 3`          | “Complex billing, multiple therapists, high fragmentation” |
| Urgent Care       | `segments includes urgent_care` + `review_count ≥ 200`         | “High throughput, scale risk, margin pressure”             |

For each playbook:

* Define **export view** in `views` table.
* Define **email subject lines** variation (3 per playbook).
* Define **call-to-action (CTA)**: “15 min ROI walk-through”.

---

## 4) Automated Sequence Logic

For each target clinic:

1. Generate export row + snippet.
2. Push to CRM (HubSpot) via CSV import + custom fields.
3. Trigger **Email 1** (template variant).
4. Wait 3 business days → if no response, send **Email 2** (follow-up with case study).
5. Wait 5 business days → LinkedIn InMail using snippet + driver highlight.
6. Record statuses in `tasks` or CRM with outcome tags (`Engaged`, `Not Interested`, `Meeting Booked`).

**Metrics to track**:

* Open/Click rate
* Reply rate
* Meeting booked rate (% of sends)
* Pipeline convert rate (if demo → pilot → contract)
* Model update: compare outcomes to `icf_score` to refine weights.

---

## 5) Feedback Loop & Model Refinement

* Add fields: `contacted_at`, `outcome`, `demo_date`, `pilot_won` in `clinics`.
* Quarterly: analyze correlations:

  * high `icf_score` & won → validate model
  * low `icf_score` but won → investigate missing features
  * high `icf_score` but lost → inspect what driver misfired
* Update `config/scoring.yaml` weights/thresholds accordingly.
* Version bump: e.g., `icf_v1.1`.

---

## 6) Dashboard Export & Hand-Off

Dashboard must enable:

* Filter clinics by playbook
* Export CSV directly
* View narrative snippet preview
* Flag “Bookmarked for outreach”
* “Mark contacted” button → updates `contacted_at`

Hand-off:

* Package a **one-pager**: “Clinic Finder for Charta GTM” highlighting how to use tool + sample exports + how to integrate into SDR/AE workflow.

---

## 7) Security & Compliance in Outbound

* Only use publicly found contacts; **no purchased email lists**.
* All outreach must comply with CAN-SPAM and state regulations.
* Store only **role-level** contacts unless individual consent is public.
* Remove duplicates & respect unsubscribes.

---

## 8) Acceptance Criteria

* One **playbook** fully implemented (e.g., Behavioral Health) with filters, templates, export.
* Dashboard enables export + snippet for at least **500 clinics**.
* Tracking of send/outcome data integrated.
* Feedback loop triggered (simple label update).
* Demo script ready: show list → snippet → CRM import → tracking → iteration.

---

## 9) Why This Matters to Charta

* Bridges analytics (clinic fit) → **GTM execution** (outbound readiness) — shows you’re not just building data but **driving pipeline**.
* Aligns with Charta’s demand-gen role: segmentation, messaging, cadence.
* Demonstrates **scrappy build + immediate utility**: exportable today, iteratable tomorrow.

