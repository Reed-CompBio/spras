# Fixed-m, two-component logistic PCA for SPRAS.

# Read command-line arguments.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 5L) {
  stop("Usage: run_lpca.R <input.csv> <scores.csv> <k=2> <m> <deviance.txt>")
}
input_file <- args[1]
output_file <- args[2]
k <- as.numeric(args[3])
m <- as.numeric(args[4])
deviance_file <- args[5]
if (!is.finite(k) || k != 2) {
  stop("k must be exactly 2.")
}
if (!is.finite(m) || m <= 0) {
  stop("m must be finite and positive; m=0 requests estimation.")
}

# Read labels as text and convert only the binary feature columns to numbers.
data <- read.csv(input_file, row.names = NULL, check.names = FALSE,
                 colClasses = "character", na.strings = character(),
                 fill = FALSE, blank.lines.skip = FALSE)
# Require at least 3 runs and 3 edge features, plus the run-label column.
if (nrow(data) < 3L || ncol(data) < 4L) {
  stop("LPCA requires at least 3 runs and 3 binary edge features.")
}
row_labels <- data[[1]]
if (anyNA(row_labels) || any(!nzchar(trimws(row_labels))) ||
    anyDuplicated(row_labels)) {
  stop("Run labels must be nonempty and unique.")
}
data_matrix <- as.matrix(data[, -1, drop = FALSE])
storage.mode(data_matrix) <- "double"
if (any(!is.finite(data_matrix)) || any(!data_matrix %in% c(0, 1))) {
  stop("Edge features must be complete, finite numeric zeros or ones.")
}
if (nrow(unique(data_matrix)) < 3L) {
  stop("LPCA requires at least 3 distinct binary network profiles.")
}

# Fit LPCA. The package can roll back and truncate the loss trace on failure,
# so retain the specific deviance-increase warning check.
max_iters <- 1000L
conv_criteria <- 1e-5
set.seed(42)
model <- withCallingHandlers(
  logisticPCA::logisticPCA(
    data_matrix, k = k, m = m, main_effects = TRUE,
    partial_decomp = TRUE, random_start = FALSE,
    max_iters = max_iters, conv_criteria = conv_criteria
  ),
  warning = function(w) {
    if (grepl("Algorithm stopped because deviance increased",
              conditionMessage(w), fixed = TRUE)) {
      stop("LPCA deviance increased during optimization.")
    }
  }
)

# Check the results and convergence before writing outputs.
scores <- model$PCs
percent_deviance <- 100 * model$prop_deviance_expl
if (!identical(dim(scores), c(nrow(data_matrix), 2L)) ||
    any(!is.finite(scores)) || !is.finite(percent_deviance)) {
  stop("LPCA returned invalid scores or deviance explained.")
}
loss <- model$loss_trace
if (length(loss) < 2L || any(!is.finite(loss))) {
  stop("LPCA returned an invalid loss trace.")
}
changes <- diff(loss)
if (any(changes > 1e-10)) {
  stop("LPCA deviance increased during optimization.")
}
if (abs(tail(changes, 1L)) >= conv_criteria) {
  stop(sprintf("LPCA did not converge within %d iterations.", max_iters))
}

# Python formats the public coordinate table.
score_table <- data.frame(datapoint_labels = row_labels,
                          PC1 = scores[, 1], PC2 = scores[, 2])
summary <- c(
  sprintf("components: %d", k),
  sprintf("m: %.17g", m),
  sprintf("percent_deviance_explained: %.17g", percent_deviance)
)
write.csv(score_table, output_file, row.names = FALSE)
writeLines(summary, deviance_file)

cat("LPCA done! Scores saved to", output_file, "\n")
cat("Score dimensions:", nrow(scores), "x", k, "\n")
cat("Percent deviance explained:", percent_deviance, "\n")
cat("Iterations:", model$iters, "\n")
cat("logisticPCA version:", as.character(packageVersion("logisticPCA")), "\n")
