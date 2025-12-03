import pandas as pd
import os

FILE = "data/raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"

print("🔍 DIAGNOSING ENTITY DATA")
df = pd.read_csv(FILE, nrows=5000, usecols=['Rndrng_NPI', 'Rndrng_Prvdr_Last_Org_Name', 'Rndrng_Prvdr_Ent_Cd', 'HCPCS_Cd'])

print(f"Loaded {len(df)} rows")

print("\n📊 Entity Code Distribution:")
print(df['Rndrng_Prvdr_Ent_Cd'].value_counts(dropna=False))

print("\n📋 Sample Org Names (Entity Code = 'O'):")
print(df[df['Rndrng_Prvdr_Ent_Cd'] == 'O']['Rndrng_Prvdr_Last_Org_Name'].head(20))

print("\n📊 Top Codes for Entity Code 'O':")
org_claims = df[df['Rndrng_Prvdr_Ent_Cd'] == 'O']
print(org_claims['HCPCS_Cd'].value_counts().head(10))

print("\n📊 Top Codes for Entity Code 'I':")
ind_claims = df[df['Rndrng_Prvdr_Ent_Cd'] == 'I']
print(ind_claims['HCPCS_Cd'].value_counts().head(10))

