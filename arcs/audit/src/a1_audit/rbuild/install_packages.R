# A1 audit R image: package install / record / verify (RUN_PLAN.md v3.1 R13, R17, R30; P17). Runs at image build only.
#   Rscript install_packages.R install            install the named packages from the pinned CRAN snapshot and
#                                                 the pinned Bioconductor release; assert each one loads
#   Rscript install_packages.R record             print every installed package as TSV (package, version, priority,
#                                                 repository) to stdout
#   Rscript install_packages.R verify LOCK.tsv    an empty lock (header only) -> "record mode"; otherwise the installed
#                                                 set must equal the lock's, package by package and version by version
# No data is read. The CRAN snapshot and the Bioconductor release are the build arguments of the Dockerfile.
args <- commandArgs(trailingOnly = TRUE)
mode <- if (length(args) >= 1) args[[1]] else "install"

cran <- Sys.getenv("A1_CRAN_SNAPSHOT")
bioc <- Sys.getenv("A1_BIOC_VERSION")
stopifnot(nzchar(cran), nzchar(bioc))
stopifnot(identical(unname(getOption("repos")[["CRAN"]]), cran))   # the CRAN pin is the one in force

# The packages the WP2 readings name (R13: WGCNA::bicor; R30: GeneOverlap::testGeneOverlap). WGCNA's own
# dependencies (CRAN and Bioconductor) are resolved by BiocManager against the two pins.
BIOC_PKGS <- c("GeneOverlap")
CRAN_PKGS <- c("WGCNA")

installed_table <- function() {
  ip <- installed.packages(fields = "Repository")
  df <- data.frame(package = ip[, "Package"], version = ip[, "Version"],
                   priority = ifelse(is.na(ip[, "Priority"]), "", ip[, "Priority"]),
                   repository = ifelse(is.na(ip[, "Repository"]), "", ip[, "Repository"]),
                   stringsAsFactors = FALSE)
  df <- df[!duplicated(df$package), ]
  df[order(df$package), ]
}

if (mode == "install") {
  # The Posit snapshot is slow from this host (first build: downloads of a few MB timed out at R's 60 s default and
  # failed with "SSL connect error"); a long timeout and up to 4 attempts per batch. Every attempt reads the same
  # pinned repositories, so a retry cannot change a version.
  options(timeout = 3600)
  bin <- Sys.getenv("A1_BIOC_BINARIES")
  stopifnot(nzchar(bin))
  pkgs <- c(BIOC_PKGS, CRAN_PKGS)
  loads <- function(p) suppressWarnings(suppressMessages(requireNamespace(p, quietly = TRUE)))
  have <- function() rownames(installed.packages())
  for (a in 1:4) if (!loads("BiocManager")) install.packages("BiocManager")
  stopifnot(loads("BiocManager"))
  for (a in 1:4) if (!loads("BiocVersion")) BiocManager::install(version = bioc, ask = FALSE, update = FALSE)
  stopifnot(identical(as.character(BiocManager::version()), bioc))

  # The dependency closure is resolved against the PINNED repositories only: Bioconductor 3.20's source repositories
  # and the CRAN snapshot (BiocManager::repositories(), whose CRAN entry is the snapshot, asserted). Each package is
  # then taken from where it lives there: a CRAN package from the snapshot, never from elsewhere; a Bioconductor
  # package from Bioconductor's pre-built binaries of the same release, whose version must equal the source
  # repository's (asserted). Installed level by level in dependency order, dependencies = FALSE (the closure is
  # complete), so no repository can substitute another version.
  repos <- BiocManager::repositories()
  stopifnot(identical(unname(repos[["CRAN"]]), cran))
  ap <- available.packages(repos = repos)
  apb <- available.packages(repos = bin)
  preinstalled <- rownames(installed.packages(priority = c("base", "recommended")))
  dep_fields <- c("Depends", "Imports", "LinkingTo")
  closure <- unique(c(pkgs, unlist(tools::package_dependencies(pkgs, db = ap, which = dep_fields,
                                                                recursive = TRUE))))
  closure <- setdiff(closure, preinstalled)
  stopifnot(all(closure %in% rownames(ap)))
  is_cran <- startsWith(ap[closure, "Repository"], cran)
  bioc_set <- closure[!is_cran]
  stopifnot(all(bioc_set %in% rownames(apb)), all(apb[bioc_set, "Version"] == ap[bioc_set, "Version"]))
  direct <- tools::package_dependencies(closure, db = ap, which = dep_fields, recursive = FALSE)
  level <- setNames(rep(NA_integer_, length(closure)), closure)
  for (k in 0:length(closure)) {
    todo <- names(level)[is.na(level)]
    if (!length(todo)) break
    ok <- todo[vapply(todo, function(p) all(intersect(direct[[p]], closure) %in% names(level)[!is.na(level)]),
                      logical(1))]
    stopifnot(length(ok) > 0)   # no dependency cycle
    level[ok] <- k
  }
  cat(sprintf("A1 rbuild install: closure %d packages (%d CRAN snapshot, %d Bioconductor %s binaries), %d levels\n",
              length(closure), sum(is_cran), length(bioc_set), bioc, max(level) + 1L))
  for (k in sort(unique(level))) {
    for (a in 1:4) {
      need <- setdiff(names(level)[level == k], have())
      if (!length(need)) break
      nc <- intersect(need, closure[is_cran])
      nb <- intersect(need, bioc_set)
      if (length(nc)) install.packages(nc, repos = c(CRAN = cran), dependencies = FALSE, Ncpus = 4L)
      if (length(nb)) install.packages(nb, repos = bin, dependencies = FALSE, Ncpus = 4L)
    }
    left <- setdiff(names(level)[level == k], have())
    if (length(left)) stop(sprintf("level %d: not installed after 4 attempts: %s", k, paste(left, collapse = ", ")))
  }
  ip <- installed.packages()
  stopifnot(all(ip[closure, "Version"] == ap[closure, "Version"]))   # every version is the pinned repositories'
  for (p in pkgs) {
    if (!loads(p)) stop(sprintf("package %s does not load", p))
  }
  cat(sprintf("A1 rbuild install: done; R %s; CRAN %s; Bioconductor %s (binaries %s)\n",
              as.character(getRversion()), cran, as.character(BiocManager::version()), bin))
} else if (mode == "record") {
  df <- installed_table()
  write.table(df, stdout(), sep = "\t", quote = FALSE, row.names = FALSE)
} else if (mode == "verify") {
  stopifnot(length(args) >= 2)
  lock <- read.delim(args[[2]], colClasses = "character", na.strings = character(0))
  if (nrow(lock) == 0) {
    cat("A1 rbuild verify: lock empty (record mode); the helper writes the lock from this image\n")
  } else {
    df <- installed_table()
    miss <- setdiff(lock$package, df$package)
    extra <- setdiff(df$package, lock$package)
    m <- merge(lock[, c("package", "version")], df[, c("package", "version")], by = "package",
               suffixes = c(".lock", ".installed"))
    bad <- m[m$version.lock != m$version.installed, ]
    if (length(miss) || length(extra) || nrow(bad)) {
      cat(sprintf("A1 rbuild verify: FAIL; missing %d, extra %d, version mismatches %d\n",
                  length(miss), length(extra), nrow(bad)))
      if (nrow(bad)) print(bad)
      if (length(miss)) print(miss)
      if (length(extra)) print(extra)
      quit(status = 3)
    }
    cat(sprintf("A1 rbuild verify: pass; %d packages at the locked versions\n", nrow(lock)))
  }
} else {
  stop(sprintf("unknown mode %s", mode))
}
