# P17 / R17 / R27: the R image exercised on SYNTHETIC data: a weighted-mean map score and its Spearman rho with a map,
# computed in R (A1 audit R image; no network). This is not the paper's script (literature_gwas_analysis.R is read under
# G2 only, RUN_PLAN R17); it exercises the image on the arithmetic R27's |z|-weighted GEDAR functional performs.
#   Rscript gedar_synthetic.R IN.bin OUT.bin
# IN.bin (little-endian): int32 C (cases); per case: int32 P, int32 G; float64 X[P, G] (row-major); float64 w[G];
#   float64 y[P]. OUT.bin: per case, float64 score[P] = sum_g X[p, g] w_g / sum_g w_g, then float64 rho =
#   cor(y, score, method = "spearman").
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2)
con <- file(args[[1]], "rb")
C <- readBin(con, "integer", 1, size = 4, endian = "little")
out <- numeric(0)
for (k in seq_len(C)) {
  PG <- readBin(con, "integer", 2, size = 4, endian = "little")
  X <- matrix(readBin(con, "double", PG[1] * PG[2], size = 8, endian = "little"), nrow = PG[1], byrow = TRUE)
  w <- readBin(con, "double", PG[2], size = 8, endian = "little")
  y <- readBin(con, "double", PG[1], size = 8, endian = "little")
  score <- as.numeric(X %*% w) / sum(w)
  out <- c(out, score, cor(y, score, method = "spearman"))
}
extra <- readBin(con, "raw", 1)
close(con)
stopifnot(length(extra) == 0)
writeBin(out, args[[2]], size = 8, endian = "little")
