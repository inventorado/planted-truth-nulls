# P17 / R13: WGCNA::bicor on synthetic vector pairs (A1 audit R image; synthetic data only; no network).
#   Rscript wgcna_bicor.R IN.bin OUT.bin META.txt
# IN.bin (little-endian): int32 K; int32 lengths[K]; then per pair k: float64 x[1..n_k], float64 y[1..n_k].
# OUT.bin: float64 [2K]: per pair, bicor(x, y, robustX = TRUE, robustY = TRUE, maxPOutliers = 1,
#   pearsonFallback = "individual") (R13's pinned values, given explicitly) and bicor(x, y) (every argument at
#   WGCNA's default), in that order.
# META.txt: WGCNA version, R version and the defaults of bicor's formals as deparsed by R.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3)
suppressPackageStartupMessages(library(WGCNA))
con <- file(args[[1]], "rb")
K <- readBin(con, "integer", 1, size = 4, endian = "little")
L <- readBin(con, "integer", K, size = 4, endian = "little")
res <- numeric(2 * K)
for (k in seq_len(K)) {
  x <- readBin(con, "double", L[k], size = 8, endian = "little")
  y <- readBin(con, "double", L[k], size = 8, endian = "little")
  stopifnot(length(x) == L[k], length(y) == L[k])
  a <- suppressWarnings(WGCNA::bicor(x, y, robustX = TRUE, robustY = TRUE, maxPOutliers = 1,
                                     pearsonFallback = "individual"))
  b <- suppressWarnings(WGCNA::bicor(x, y))
  res[2 * k - 1] <- as.numeric(a)
  res[2 * k] <- as.numeric(b)
}
extra <- readBin(con, "raw", 1)
close(con)
stopifnot(length(extra) == 0)   # the whole input was consumed
writeBin(res, args[[2]], size = 8, endian = "little")
f <- formals(WGCNA::bicor)
meta <- c(sprintf("WGCNA\t%s", as.character(packageVersion("WGCNA"))),
          sprintf("R\t%s", as.character(getRversion())),
          sprintf("K\t%d", K),
          sprintf("formal\trobustX\t%s", paste(deparse(f$robustX), collapse = " ")),
          sprintf("formal\trobustY\t%s", paste(deparse(f$robustY), collapse = " ")),
          sprintf("formal\tmaxPOutliers\t%s", paste(deparse(f$maxPOutliers), collapse = " ")),
          sprintf("formal\tpearsonFallback\t%s", paste(deparse(f$pearsonFallback), collapse = " ")))
writeLines(meta, args[[3]])
