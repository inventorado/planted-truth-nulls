# P17 / R22, R30: R's fisher.test on synthetic 2 x 2 tables (A1 audit R image; synthetic data only).
#   Rscript fisher.R TABLES.tsv OUT.tsv
# TABLES.tsv: header case, a, b, c, d (matrix(c(a, c, b, d), 2): rows in list / not, columns in term / not).
# OUT.tsv: case, p_two_sided, p_greater, p_less, estimate (the conditional MLE odds ratio), 17 significant digits.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2)
tb <- read.delim(args[[1]], colClasses = c("character", rep("integer", 4)))
fmt <- function(v) sprintf("%.17g", v)
rows <- lapply(seq_len(nrow(tb)), function(i) {
  m <- matrix(c(tb$a[i], tb$c[i], tb$b[i], tb$d[i]), nrow = 2)
  two <- fisher.test(m, alternative = "two.sided")
  gr <- fisher.test(m, alternative = "greater")
  le <- fisher.test(m, alternative = "less")
  data.frame(case = tb$case[i], p_two_sided = fmt(two$p.value), p_greater = fmt(gr$p.value),
             p_less = fmt(le$p.value), estimate = fmt(unname(two$estimate)), stringsAsFactors = FALSE)
})
write.table(do.call(rbind, rows), args[[2]], sep = "\t", quote = FALSE, row.names = FALSE)
