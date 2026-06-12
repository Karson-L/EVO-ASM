import pandas as pd, os
os.chdir(r"c:\seelf\大三下\主修毕设")
path = os.path.join("results", "e4_full_evolution", "p_mut=0.05_lambda=1.00_sigma=0.02_seed=42")
agents = pd.read_csv(os.path.join(path, "agents.csv"))
families = pd.read_csv(os.path.join(path, "families.csv"))
anc_set = set(agents["ancestor_id"].unique())
fam_set = set(families["family_id"].unique())
print("ancestor ids:", sorted(anc_set)[:20], "... count:", len(anc_set))
print("family ids total:", len(fam_set))
print("in fam but not anc:", sorted(fam_set - anc_set)[:20], "... count:", len(fam_set - anc_set))
print("in anc but not fam:", sorted(anc_set - fam_set))
# Check if agent step matches
print("agent step unique:", agents["step"].unique())
print("family step unique:", families["step"].unique())
