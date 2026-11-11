# P17 / R30: GeneOverlap's source and testGeneOverlap on synthetic gene lists (A1 audit R image; synthetic data only).
#   Rscript geneoverlap.R CASES.tsv OUT.tsv SOURCE.txt
# CASES.tsv: header case, genome_size, list_a, list_b; genome_size "NA" = GeneOverlap's default; lists are
#   comma-joined synthetic tokens (g00001 ...). OUT.tsv: case, pval, odds_ratio, intersection, union, genome_size,
#   jaccard (pval / odds_ratio printed with 17 significant digits).
# SOURCE.txt: every function of the GeneOverlap namespace and every method of its S4 generics, deparsed, preceded by
#   the package version: the text R30's direction and default genome size are read from.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3)
suppressPackageStartupMessages(library(GeneOverlap))
ns <- asNamespace("GeneOverlap")
src <- c(sprintf("# GeneOverlap %s; R %s", as.character(packageVersion("GeneOverlap")),
                 as.character(getRversion())))
for (nm in sort(ls(ns, all.names = TRUE))) {
  obj <- get(nm, envir = ns)
  if (is.function(obj)) {
    src <- c(src, sprintf("## function %s", nm), deparse(obj))
  }
}
for (g in c("testGeneOverlap", "newGeneOverlap", "getContbl", "show", "print")) {
  if (isGeneric(g, where = ns)) {
    ms <- findMethods(g, where = ns)
    for (sig in names(ms)) {
      src <- c(src, sprintf("## method %s(%s)", g, sig), deparse(ms[[sig]]@.Data))
    }
  }
}
writeLines(src, args[[3]])

cases <- read.delim(args[[1]], colClasses = "character", na.strings = character(0))
out <- data.frame(case = character(0), pval = character(0), odds_ratio = character(0), intersection = integer(0),
                  union = integer(0), genome_size = numeric(0), jaccard = character(0), stringsAsFactors = FALSE)
for (i in seq_len(nrow(cases))) {
  A <- strsplit(cases$list_a[i], ",", fixed = TRUE)[[1]]
  B <- strsplit(cases$list_b[i], ",", fixed = TRUE)[[1]]
  go <- if (cases$genome_size[i] == "NA") newGeneOverlap(A, B) else
    newGeneOverlap(A, B, genome.size = as.integer(cases$genome_size[i]))
  go <- testGeneOverlap(go)
  out[i, "case"] <- cases$case[i]
  out[i, "pval"] <- sprintf("%.17g", getPval(go))
  out[i, "odds_ratio"] <- sprintf("%.17g", getOddsRatio(go))
  out[i, "intersection"] <- length(getIntersection(go))
  out[i, "union"] <- length(getUnion(go))
  out[i, "genome_size"] <- getGenomeSize(go)
  out[i, "jaccard"] <- sprintf("%.17g", getJaccard(go))
}
write.table(out, args[[2]], sep = "\t", quote = FALSE, row.names = FALSE)
