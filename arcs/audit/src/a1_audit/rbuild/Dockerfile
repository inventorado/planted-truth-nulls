# A1 audit R image (arcs/audit/RUN_PLAN.md v3.1 FROZEN: R13, R17, R30; plant P17). WP2 build, SYNTHETIC DATA ONLY.
#
# R17 reading: "The script runs in a Docker R image pinned by digest. Use rocker/r-ver, whose CRAN is date-locked ...
# The R version is the one the repository declares; if it declares none, the R release current at the commit date.
# CRAN packages come from the Posit Package Manager snapshot of the commit date; Bioconductor from the release matching
# that R." The repository's declared R version, its commit date and the script's package list are read under G2 only
# (R17: "The script is read under G2 only for its package list and inputs"), so they are NOT known at WP2. This WP2
# image is therefore PROVISIONAL for R17: R 4.4.3 (rocker/r-ver:4.4.3, its own date-locked CRAN snapshot 2025-04-10)
# and Bioconductor 3.20 (the release matching R 4.4). It carries the packages the readings name now: WGCNA (R13's
# WGCNA::bicor) and GeneOverlap (R30's testGeneOverlap, read from its source). Under G2 (WP4) the build arguments
# below are reset to the repository's R version / commit-date snapshot and the script's package list is added; the
# helper build_image.py records every value. Nothing here reads or copies any data.
#
# Base pinned by digest (pulled 2026-10-01; `docker pull rocker/r-ver:4.4.3` -> this digest).
ARG BASE=rocker/r-ver:4.4.3@sha256:3dae5d2eeddf74f10e0a81fb6b7ae350295e288000304f438b844b2c1e00fe2c
FROM ${BASE}

ARG CRAN_SNAPSHOT=https://p3m.dev/cran/__linux__/noble/2025-04-10
ARG BIOC_VERSION=3.20
# Bioconductor's own pre-built Linux binaries of the same release (the binaries Bioconductor builds for its
# bioconductor_docker 3.20 image: R 4.4, x86_64-pc-linux-gnu). Needed because rocker/r-ver ships no zlib headers, so
# XVector (-> Biostrings -> KEGGREST -> AnnotationDbi -> GO.db, all imports of WGCNA) cannot be compiled from source
# here (first build, logs/build_20261001T205657Z_pass1.log: "zlib.h: No such file or directory"), and no system
# package is installed (the WP2 network allowance covers base images and CRAN / Bioconductor packages only). Same
# release, same package versions (the lock records them); the source repositories stay behind it.
ARG BIOC_BINARIES=https://bioconductor.org/packages/3.20/container-binaries/bioconductor_docker
ENV A1_CRAN_SNAPSHOT=${CRAN_SNAPSHOT} \
    A1_BIOC_VERSION=${BIOC_VERSION} \
    A1_BIOC_BINARIES=${BIOC_BINARIES} \
    OMP_NUM_THREADS=1

# CRAN is pinned explicitly (the same snapshot rocker/r-ver:4.4.3 locks; asserted by install_packages.R).
RUN echo "options(repos = c(CRAN = '${CRAN_SNAPSHOT}'), BiocManager.check_repositories = FALSE)" \
        >> /usr/local/lib/R/etc/Rprofile.site

COPY install_packages.R /opt/a1_rbuild/install_packages.R
RUN Rscript /opt/a1_rbuild/install_packages.R install && \
    Rscript /opt/a1_rbuild/install_packages.R record > /opt/a1_rbuild/installed_versions.tsv

# Version pin: once packages.lock.tsv exists, every package it lists must be installed at exactly that version (the
# build fails otherwise). The first build runs with an empty lock ("record" mode) and the helper writes the lock.
COPY packages.lock.tsv /opt/a1_rbuild/packages.lock.tsv
RUN Rscript /opt/a1_rbuild/install_packages.R verify /opt/a1_rbuild/packages.lock.tsv

WORKDIR /work
CMD ["Rscript", "-e", "sessionInfo()"]
