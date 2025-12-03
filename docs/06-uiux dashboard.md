# 06_UI_UX_Dashboard.md — **Delightful, “Charta-grade” UI/UX** (Next.js + Tailwind)

> Goal: a **distinctive, premium** GTM dashboard that looks like it belongs at Charta: fast, clean, **evidence-first**, and **instantly shows value** (fit, “why now”, easy export).

---

## 0) Brand System (tokens you can drop into Tailwind)

> These are tasteful **placeholders** inspired by modern healthtech. Swap with Charta’s official hexes later.

```ts
// tailwind.config.ts (extend.theme.colors)
charta: {
  ink: "#0F172A",        // deep navy for headings (#0F172A slate-900)
  night: "#111827",      // near-black for backgrounds
  slate: "#334155",      // body text
  mist: "#E5E7EB",       // dividers
  cloud: "#F8FAFC",      // page bg
  blue: "#2563EB",       // primary action / links
  teal: "#0D9488",       // emphasis / positive
  amber: "#F59E0B",      // warning / attention
  rose: "#F43F5E",       // risk / denial pressure
  leaf: "#10B981",       // success / ROI
}
```

**Typography**

* Headings: `font-sans` medium weight, tracking-tight
* Body: `text-slate-700` on `cloud` background
* Numerics (scores/KPIs): `tabular-nums` for alignment

**Elevation & Corners**

* Cards: `rounded-2xl shadow-[0_6px_30px_rgba(2,6,23,.06)]`
* Buttons/chips: `rounded-xl`
* Inputs: subtle inner shadow on focus

**Motion**

* Use **Framer Motion** for fades/slides (`duration=0.25–0.35s`)
* Microinteractions: hover lifts `translate-y-[-1px]` + soft shadow

---

## 1) Signature Look & Feel (what makes it “Charta”)

* **Evidence-first design**: each high score shows **why** with labeled driver chips and **one-click source**.
* **KPI header strip** that **quantifies value** for the current filter (e.g., “Est. RVU Uplift Range”, “EMR Compatibility”, “Denial Heat”).
* **Driver Pills** with color semantics:

  * EMR friction → `teal` (path to integrate)
  * Denial pressure → `rose`
  * Segment fit → `blue`
  * Scale/velocity → `amber` or `leaf`
* **Narrative composer** (right rail) that builds a 2-line, on-brand pitch from data.

---

## 2) Information Architecture

**Routes**

* `/` — **Leads** (table + filters + KPI header)
* `/clinic/[id]` — **Clinic Detail** (facts, drivers, evidence, map)
* `/views` — Saved Views
* `/exports` — Export History

**Primary Objects**

* **Clinic row** (open detail)
* **Saved view** (pre-filtered segment packs)
* **Export job** (CSV with parameters)

---

## 3) Screens & Components

### A) Leads (Home)

**Layout**

* **Header KPI strip** (always visible)
* **Filters rail** (left)
* **Leads table** (center)
* **Narrative rail** (right, collapsible)

**Header KPI Strip** *(show value immediately)*

* **Projected RVU Range** (from score mix): `+8–15%` badge
* **Top Driver Mix**: pills (e.g., “Denial ↑”, “Common EMR”, “BH Segment”)
* **Export CTA**: “Export N clinics” primary button

```tsx
// <MetricBanner />
<div className="grid grid-cols-3 gap-3">
  <KpiCard title="Projected RVU Uplift" value="+8–15%" tone="leaf" />
  <KpiCard title="Top Drivers" value={<DriverPills /* chips */ />} />
  <Button className="justify-self-end bg-charta-blue text-white">Export {count} Clinics</Button>
</div>
```

**Filters Rail**

* Segments (chips, multi): Primary, BH, Home Health, Urgent
* States (multi-select)
* ICF slider (default 70–100)
* EMR (multi: Epic, athena, NextGen, eCW, etc.)
* Size buckets (1, 2–5, 6–10, 10+)
* Flags: Medicare, Medicaid, ACO
* **Saved Views** dropdown (quick switch)

**Table Columns (default)**

* **Brand** (logo letter avatar)
* **Segments** (tiny chips)
* **State**
* **Locations**
* **Providers (proxy)**
* **EMR**
* **ICF** (color-coded badge: 80+ leaf / 60–79 amber / else slate)
* **Drivers** (max 2 compact pills; hover to expand)
* **Actions**: Open ▸, Export, Bookmark

**Right Narrative Rail**

* Selected rows → **dynamic 2-line pitch** (editable)
* Copy button + “Add to export”
* Shows **evidence links** used in the pitch (builds trust)

---

### B) Clinic Detail

**Header**

* Brand + segment chips + **ICF badge**
* **One-tap actions**: Copy pitch, Export this clinic

**Tabs**

1. **Overview**

   * Facts grid: EMR, locations, providers proxy, payer flags
   * **Driver list** (ranked with color) + *because-of* snippets
   * “Integration Path Hypothesis” box (e.g., “athenahealth; bidirectional pre-bill review feasible”)

2. **Locations**

   * Map (Leaflet) clusters
   * Location cards with phone/hours

3. **Evidence**

   * **EvidenceCard** components: title, snippet, domain, open icon
   * Filter by type: `emr_hint`, `denial`, `services`, `hiring`

4. **Notes**

   * Freeform notepad + “Mark Contacted” toggle (for GTM loop)

---

### C) Saved Views

* Grid of cards with **human labels**:

  * “Behavioral Health — TX — ICF ≥ 75”
  * “Home Health — Medicare — 3+ sites”
* Each shows **count**, **avg ICF**, **top driver mix** bars

---

## 4) “Signature” Components (with Tailwind classes)

**ScoreBadge**

```tsx
<div className={cn(
  "inline-flex items-center rounded-xl px-2.5 py-1 text-sm font-medium tabular-nums",
  score>=80 ? "bg-charta-leaf/10 text-charta-leaf" :
  score>=60 ? "bg-charta-amber/10 text-charta-amber" :
              "bg-charta-slate/10 text-charta-slate"
)}>
  {score}
</div>
```

**DriverPill**

```tsx
<span className={cn(
  "inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs",
  type==="denial" && "bg-charta-rose/10 text-charta-rose",
  type==="emr"    && "bg-charta-teal/10 text-charta-teal",
  type==="segment"&& "bg-charta-blue/10 text-charta-blue",
  type==="scale"  && "bg-charta-amber/10 text-charta-amber"
)}>
  {label}
</span>
```

**EvidenceCard**

```tsx
<div className="rounded-2xl border border-charta-mist bg-white p-4 hover:shadow-md transition">
  <div className="flex items-center justify-between">
    <h4 className="font-medium text-charta-ink">{title}</h4>
    <a href={url} target="_blank" className="text-charta-blue text-sm">Open ↗</a>
  </div>
  <p className="mt-2 text-sm text-slate-600 line-clamp-3">{snippet}</p>
  <div className="mt-3 text-xs text-slate-500">{domain} · {capturedAt}</div>
</div>
```

**MetricBanner (KPI)**

```tsx
<div className="rounded-2xl bg-white p-4 border border-charta-mist">
  <div className="text-xs uppercase text-slate-500">{title}</div>
  <div className={cn("mt-1 text-2xl font-semibold",
    tone==="leaf" && "text-charta-leaf",
    tone==="rose" && "text-charta-rose",
    tone==="amber"&& "text-charta-amber"
  )}>{value}</div>
</div>
```

---

## 5) Microcopy & Empty States (make value obvious)

* **Empty leads**: “No clinics match this filter. Try ICF ≥ 60 or add more segments.”
* **No evidence**: “We haven’t captured evidence yet. Add a quick research task.”
* **ICF helper tooltip**: “ICF ranks clinics by expected value from pre-bill AI review (fit × urgency × speed to integrate).”
* **Export success**: “CSV with 287 clinics is ready. It includes 2-line narrative & evidence links.”

---

## 6) Accessibility & Performance

* Color contrast compliant on score badges & pills
* Keyboard focus rings: `focus-visible:ring-2 ring-charta-blue`
* Server-side pagination; debounce filters; suspense loading skeletons
* Prefetch clinic detail on row hover for snappy open

---

## 7) “Showcase Value” Patterns

* **Contextual value math** (top of page):

  * “For your current view (N clinics), **estimated RVU gain**: +X% to +Y%.”
  * “**EMR compatibility**: 68% on common vendors → shorter onboarding.”
  * “**Denial heat**: 41% high/med → stronger urgency.”

* **Explainable top drivers** on every row → leadership trust.

* **One-click narrative** → sales can move immediately.

---

## 8) Page-level Wireframe (text)

```
┌───────────────────────────────────────────────────────────────────────┐
│  [Projected RVU +8–15%]   [Top Drivers: Denial↑, Common EMR]   [Export]│
├──── Filters ────────────────┬────────── Leads Table ───────────────────┬─ Narrative ──┤
│ Segments  ◻PC ◻BH ◻HH ◻UC   │ Brand     Seg  State  Loc  Prov  EMR  ICF│  “We identified …”    │
│ States    [TX, CO, FL]      │ ───────────────────────────────────────── │  [Copy] [Add to Export]│
│ ICF      [70–100]           │ Family…  BH   TX     5    42    ath  91 │  Evidence: [1][2]     │
│ EMR       [Epic, ath, …]    │ Eventus… PC   CO     12   120   eCW  87 │                      │
│ Size      [2–5] [6–10]      │ Prevent… HH   FL     7    63    NXG  85 │                      │
│ Flags     ◻Medicare ◻ACO    │ …                                      … │                      │
│ [Save View] [Reset]         │ [Open][Export][★]                        │                      │
└─────────────────────────────────────────────────────────────────────────┴────────────────────────┘
```

---

## 9) Implementation Notes (Cursor-ready)

* Use **shadcn/ui** primitives where helpful (`Card`, `Badge`, `Button`).
* Icons: **lucide-react** (`Sparkles`, `Activity`, `FileDown`, `ExternalLink`).
* Map: **react-leaflet** (lazy load).
* State: **TanStack Table** for sorting/pagination; **Zustand** or URL query state for filters.
* Motion: **framer-motion** fade-in for table rows and cards.

---

## 10) Acceptance Criteria (UI/UX)

* Distinctive visual identity (tokens + components) applied consistently.
* “2-click to value”: filter + export works end-to-end.
* KPI header computes and displays **meaningful, segment-aware** metrics.
* Evidence is **one click away** from any score/driver.
* Narrative rail produces **usable** two-liner with copy/export.
* Passes basic a11y checks; performs smoothly with 5k rows (server-paginated).

---

## 11) Why this will **impress Charta**

* It feels **designed**, not just functional: premium cards, crisp motion, **evidence-first**.
* It puts **GTM value** front-and-center (uplift, denial heat, integration path).
* It’s **ready for handoff**: exports and narratives are production-useful, not mock data.

---
