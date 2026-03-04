FROM continuumio/miniconda3:24.7.1-0

LABEL maintainer="Edgardo Rosado Ramos"
LABEL description="MAGI - Multi-kingdom Analysis of Genomic Interactions"

WORKDIR /app

# Install bioinformatics tools via conda
RUN conda install -y -c bioconda -c conda-forge \
    fastp=0.23.4 \
    minimap2=2.28 \
    samtools=1.20 \
    kraken2=2.1.3 \
    bracken=2.9 \
    flye=2.9.4 \
    snakemake-minimal=8.20.1 \
    && conda clean -afy

# Install geNomad via pip
RUN pip install --no-cache-dir genomad

# Copy and install MAGI package
COPY pyproject.toml .
COPY src/ src/
COPY workflow/ workflow/
COPY config/ config/

RUN pip install --no-cache-dir .

# Default entrypoint
ENTRYPOINT ["magi"]
CMD ["--help"]
