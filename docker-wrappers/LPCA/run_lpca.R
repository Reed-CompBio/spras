# Read command line arguments
args = commandArgs(trailingOnly = TRUE)
input_file = args[1]
output_file = args[2]
k = as.integer(args[3])
m = as.numeric(args[4])

# Load data
library(logisticPCA)
data = read.csv(input_file, row.names = NULL)
row_labels = data[, 1]
data = data[, -1]
data_matrix = as.matrix(data)
data_matrix[is.na(data_matrix)] = 0

# Run LPCA
model = logisticPCA(data_matrix, k = k, m = m, partial_decomp = TRUE)

# Save scores
scores = model$PCs
rownames(scores) = row_labels
write.csv(scores, output_file, row.names = TRUE)

# Save deviance explained
deviance_file = sub("\\.csv$", "_deviance.txt", output_file)
writeLines(as.character(model$prop_deviance_expl), deviance_file)

cat("LPCA done! Scores saved to", output_file, "\n")
cat("Score dimensions:", nrow(scores), "x", ncol(scores), "\n")
cat("Proportion of deviance explained:", model$prop_deviance_expl, "\n")