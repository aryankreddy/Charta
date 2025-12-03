import pandas as pd

FILE = "data/raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"

print("🔍 CHECKING COLUMNS AND NAMES")
# Read header only
header = pd.read_csv(FILE, nrows=0).columns.tolist()
print(f"Columns: {header}")

if 'Rndrng_Prvdr_St1' in header:
    print("✅ Street Address Found")
else:
    print("❌ Street Address NOT Found")

# Check for Type 1s with Corp Names
CORP_MARKERS = ['LLC', 'INC', 'PA', 'GROUP', 'CLINIC', 'CENTER', 'HOSPITAL', 'HEALTH', 'ASSOCIATES']

def is_corp(name):
    if pd.isna(name): return False
    return any(m in str(name).upper().split() for m in CORP_MARKERS)

print("\n🔍 Scanning first 10k rows for Type 1 Corp Names...")
df = pd.read_csv(FILE, nrows=10000, usecols=['Rndrng_Prvdr_Last_Org_Name', 'Rndrng_Prvdr_Ent_Cd'])

type1_corps = df[(df['Rndrng_Prvdr_Ent_Cd'] == 'I') & (df['Rndrng_Prvdr_Last_Org_Name'].apply(is_corp))]
print(f"Found {len(type1_corps)} Type 1 rows with Corporate Names")
print(type1_corps['Rndrng_Prvdr_Last_Org_Name'].head(10))
