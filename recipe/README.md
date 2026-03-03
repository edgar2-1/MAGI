# Bioconda Recipe for MAGI

This directory contains the Bioconda recipe template for submitting MAGI to the
[Bioconda](https://bioconda.github.io/) channel.

## How to Submit

1. Fork [bioconda-recipes](https://github.com/bioconda/bioconda-recipes)
2. Copy this `meta.yaml` to `recipes/magi-metagenomics/meta.yaml` in the fork
3. Update the `sha256` hash with the actual PyPI tarball hash:
   ```bash
   pip download magi-metagenomics --no-deps --no-binary :all:
   sha256sum magi-metagenomics-*.tar.gz
   ```
4. Submit a pull request to bioconda-recipes
5. Follow the [Bioconda contribution guidelines](https://bioconda.github.io/contributor/index.html)

## Testing Locally

```bash
conda install -c conda-forge conda-build
conda build recipe/
```
