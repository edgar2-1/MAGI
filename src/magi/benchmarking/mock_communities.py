"""Known mock community compositions for benchmarking."""

# ZymoBIOMICS Microbial Community Standard (D6300)
# Expected relative abundances at species level (theoretical)
ZYMO_D6300 = {
    "name": "ZymoBIOMICS Microbial Community Standard",
    "catalog": "D6300",
    "kingdom": "bacteria",
    "expected": {
        "Listeria_monocytogenes": 0.12,
        "Pseudomonas_aeruginosa": 0.12,
        "Bacillus_subtilis": 0.12,
        "Escherichia_coli": 0.12,
        "Salmonella_enterica": 0.12,
        "Lactobacillus_fermentum": 0.12,
        "Enterococcus_faecalis": 0.12,
        "Staphylococcus_aureus": 0.12,
    },
    "expected_fungi": {
        "Saccharomyces_cerevisiae": 0.02,
        "Cryptococcus_neoformans": 0.02,
    },
}

# ZymoBIOMICS Gut Microbiome Standard (D6331)
ZYMO_D6331 = {
    "name": "ZymoBIOMICS Gut Microbiome Standard",
    "catalog": "D6331",
    "kingdom": "bacteria",
    "expected": {
        "Akkermansia_muciniphila": 0.001,
        "Bacteroides_fragilis": 0.057,
        "Bifidobacterium_adolescentis": 0.171,
        "Clostridioides_difficile": 0.057,
        "Clostridium_perfringens": 0.171,
        "Enterococcus_faecalis": 0.057,
        "Escherichia_coli": 0.171,
        "Fusobacterium_nucleatum": 0.057,
        "Lactobacillus_fermentum": 0.171,
        "Prevotella_melaninogenica": 0.057,
        "Salmonella_enterica": 0.001,
        "Staphylococcus_aureus": 0.001,
        "Veillonella_rogosae": 0.028,
    },
}

MOCK_COMMUNITIES = {
    "zymo_d6300": ZYMO_D6300,
    "zymo_d6331": ZYMO_D6331,
}
