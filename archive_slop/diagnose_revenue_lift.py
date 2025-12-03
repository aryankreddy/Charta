import pandas as pd
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCORED_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")

def diagnose():
    if not os.path.exists(SCORED_FILE):
        print("❌ Scored file not found.")
        return

    print("🔍 Diagnosing Revenue Lift Data...")
    df = pd.read_csv(SCORED_FILE, low_memory=False)
    
    # Filter: Top 500 Tier 1 & Tier 2 (Same logic as update_frontend_data.py)
    top_clinics = df.sort_values('icp_score', ascending=False).head(500)
    
    print(f"Analyzing Top {len(top_clinics)} Clinics...")
    
    # Check Revenue
    has_rev = top_clinics[top_clinics['metric_est_revenue'] > 0]
    print(f"\n💰 Revenue Data:")
    print(f"  - Clinics with Revenue > $0: {len(has_rev)} ({len(has_rev)/len(top_clinics)*100:.1f}%)")
    print(f"  - Mean Revenue: ${top_clinics['metric_est_revenue'].mean():,.2f}")
    
    # Check Undercoding
    has_coding = top_clinics[top_clinics['undercoding_ratio'] > 0]
    print(f"\n📉 Undercoding Data:")
    print(f"  - Clinics with Undercoding > 0: {len(has_coding)} ({len(has_coding)/len(top_clinics)*100:.1f}%)")
    print(f"  - Mean Undercoding: {top_clinics['undercoding_ratio'].mean():.4f}")
    
    # Check Lift Calculation
    # Lift = Revenue * Undercoding % * 0.2
    top_clinics['lift_val'] = top_clinics['metric_est_revenue'] * top_clinics['undercoding_ratio'] * 0.2
    has_lift = top_clinics[top_clinics['lift_val'] > 0]
    
    print(f"\n🚀 Revenue Lift:")
    print(f"  - Clinics with Lift > $0: {len(has_lift)} ({len(has_lift)/len(top_clinics)*100:.1f}%)")
    print(f"  - Mean Lift: ${top_clinics['lift_val'].mean():,.2f}")
    
    # Sample of 0 Lift
    zero_lift = top_clinics[top_clinics['lift_val'].isna() | (top_clinics['lift_val'] == 0)].head(5)
    if not zero_lift.empty:
        print("\n⚠️ Sample Clinics with $0 Lift:")
        print(zero_lift[['org_name', 'metric_est_revenue', 'undercoding_ratio', 'lift_val']].to_string())

if __name__ == "__main__":
    diagnose()
