#!/usr/bin/env python3
"""Generate synthetic standardized abundance data for the MAGI example."""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

samples = [f"sample_{i:02d}" for i in range(1, 11)]

# Bacteria: 4 species with different abundance patterns between groups
bacteria_taxa = {
    "Escherichia_coli": {"healthy": (150, 40), "disease": (80, 30)},
    "Staphylococcus_aureus": {"healthy": (30, 15), "disease": (120, 35)},
    "Lactobacillus_rhamnosus": {"healthy": (200, 50), "disease": (60, 25)},
    "Bacteroides_fragilis": {"healthy": (100, 30), "disease": (90, 25)},
}

fungi_taxa = {
    "Candida_albicans": {"healthy": (10, 5), "disease": (80, 25)},
    "Aspergillus_niger": {"healthy": (15, 8), "disease": (45, 15)},
    "Saccharomyces_cerevisiae": {"healthy": (25, 10), "disease": (20, 8)},
    "Malassezia_restricta": {"healthy": (8, 4), "disease": (35, 12)},
}

virus_taxa = {
    "Phage_T4": {"healthy": (5, 3), "disease": (25, 10)},
    "CrAssphage": {"healthy": (40, 15), "disease": (15, 8)},
    "SARS_CoV2": {"healthy": (0, 1), "disease": (3, 2)},
    "Torque_teno_virus": {"healthy": (12, 6), "disease": (30, 10)},
}

groups = ["healthy"] * 5 + ["disease"] * 5
taxid_counter = 100


def generate_kingdom(taxa_dict, kingdom, method):
    global taxid_counter
    rows = []
    for taxon, group_params in taxa_dict.items():
        for i, sample in enumerate(samples):
            group = groups[i]
            mean, std = group_params[group]
            abundance = max(0, int(np.random.normal(mean, std)))
            rows.append({
                "SampleID": sample,
                "Kingdom": kingdom,
                "Taxon": taxon,
                "NCBI_TaxID": taxid_counter,
                "Rank": "species",
                "Abundance": abundance,
                "Method": method,
            })
        taxid_counter += 1
    return pd.DataFrame(rows)


df_bac = generate_kingdom(bacteria_taxa, "bacteria", "kraken2")
df_fun = generate_kingdom(fungi_taxa, "fungi", "kraken2")
df_vir = generate_kingdom(virus_taxa, "virus", "genomad")

df_bac.to_csv(data_dir / "standardized_bacteria.tsv", sep="\t", index=False)
df_fun.to_csv(data_dir / "standardized_fungi.tsv", sep="\t", index=False)
df_vir.to_csv(data_dir / "standardized_virus.tsv", sep="\t", index=False)

print(f"Generated {len(df_bac)} bacteria records")
print(f"Generated {len(df_fun)} fungi records")
print(f"Generated {len(df_vir)} virus records")
print(f"Data written to {data_dir}")
