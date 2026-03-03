# MAGI Cluster Profiles

Snakemake cluster profiles for running MAGI on HPC systems.

## SLURM

```bash
# Run with SLURM profile
magi --config config.yaml run --cores 100
# Or directly:
snakemake --profile workflow/profiles/slurm --configfile config.yaml
```

Edit `workflow/profiles/slurm/config.yaml` to set:
- `slurm_partition` -- your cluster's partition name
- Memory and runtime limits per rule
- `jobs` -- max concurrent jobs

## SGE (Sun Grid Engine)

```bash
snakemake --profile workflow/profiles/sge --configfile config.yaml
```

Edit `workflow/profiles/sge/config.yaml` to set:
- Parallel environment name (`-pe smp`)
- Memory and runtime limits
- `jobs` -- max concurrent jobs

## Custom Profiles

Copy any profile directory and modify `config.yaml` for your cluster.
See the [Snakemake documentation](https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles) for all options.
