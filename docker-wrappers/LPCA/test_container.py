#!/usr/bin/env python3
"""Run standalone regression tests for the SPRAS LPCA container.

Save this file beside run_lpca.R in docker-wrappers/LPCA/. From the repository
root, build the image and run the tests with Python >= 3.9 and Docker:
    docker build -t reedcompbio/lpca:v1 docker-wrappers/LPCA
    python docker-wrappers/LPCA/test_container.py

The wrapper is located relative to this file, not the working directory.
Results go to the terminal; --log PATH also saves them to a new UTF-8 file.
Use --image TAG to select a different already-built local image. Tests never
pull an image or require a registry login.

The runner checks the local/container wrapper match (ignoring CRLF vs LF),
package versions, numerical regressions, and input/output behavior. All
fixtures are created inside one disposable Linux container, with no network
or host mounts. Local R, pytest, and an installed SPRAS package are not needed.
Each fit runs the real five-argument CLI in a separate Rscript process; the
production wrapper needs no testing hooks. Scope: fixed positive m, exactly
two components, and whole-model deviance, without CV or per-axis variance.

The process exits with zero only after a completed, passing test run. This
suite does not test SPRAS volume mapping, plotting, or Snakemake integration.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from contextlib import nullcontext
from pathlib import Path

R_TESTS = r'''
options(warn = 1)
cat("=== Environment and wrapper identity ===\n")
print(sessionInfo())
versions <- c(logisticPCA = "0.2", rARPACK = "0.11-0", RSpectra = "0.16-2")
for (pkg in names(versions)) {
  actual <- packageVersion(pkg)
  cat(pkg, as.character(actual), "\n")
  if (actual != package_version(versions[[pkg]])) {
    stop(paste("Unexpected package version:", pkg))
  }
}

# Compare exact source bytes except for Windows CRLF versus Unix LF newlines.
source_file <- "/app/run_lpca.R"
source_bytes <- readBin(source_file, "raw", n = file.info(source_file)$size)
source_text <- gsub("\r\n", "\n", rawToChar(source_bytes), fixed = TRUE)
normalized <- tempfile()
writeBin(charToRaw(source_text), normalized)
actual_md5 <- unname(tools::md5sum(normalized))
unlink(normalized)
cat("Container wrapper MD5 (LF normalized):", actual_md5, "\n")
cat("=== Wrapper source being tested ===\n", source_text, "\n", sep = "")
if (!identical(actual_md5, expected_md5)) {
  stop("The image does not contain the adjacent run_lpca.R. Rebuild the selected image.")
}
cat("Local/container wrapper match: PASS\n")

work <- tempfile(pattern = "LPCA numerical checks ")
dir.create(work)
passed <- 0L
failed <- 0L
need <- function(condition, message) {
  if (!isTRUE(condition)) stop(message, call. = FALSE)
}
check <- function(name, action) {
  cat("\n===", name, "===\n")
  tryCatch({
    action()
    passed <<- passed + 1L
    cat("PASS:", name, "\n")
  }, error = function(e) {
    failed <<- failed + 1L
    cat("FAIL:", name, "|", conditionMessage(e), "\n")
  })
}
near <- function(actual, expected, tolerance, label) {
  need(length(actual) == length(expected), paste(label, "length mismatch"))
  delta <- max(abs(as.numeric(actual) - as.numeric(expected)))
  cat(label, "maximum absolute difference:", format(delta, digits = 10),
      "(tolerance", tolerance, ")\n")
  need(is.finite(delta) && delta < tolerance, paste(label, "differs from reference"))
}

# Regression reference provenance:
# The binary patterns below correspond to pathway-params-1.txt through
# pathway-params-4.txt in test/analysis/input/lpca/. The reference scores come
# from test/analysis/test_lpca.py at SPRAS commit
# 5b64162a4b93691f02615696e62f7542ddda753d.
# The deviance references were recorded on the same patterns using R 4.4.2,
# logisticPCA 0.2, rARPACK 0.11-0, and RSpectra 0.16-2 on x86_64 Linux:
#   k=2, m=4: proportion 0.9192537 (recorded console precision)
#   k=2, m=6: proportion 0.976137532256003 (recorded output-file precision)
# Both fits used main effects and partial_decomp=TRUE. These are observed
# regression results, not an independent proof of numerical correctness.
# Distances allow a global orthogonal change of axes. Absolute tolerances are
# 1e-3 for reference distances and deviance percentages and 1e-6 for repeated
# fits. Investigate changes before updating references or loosening tolerances,
# especially when updating the numerical package versions above.
x <- rbind(
  c(1,1,1,1,1,0,0,0,0,0,0),
  c(1,1,0,0,0,1,1,1,0,0,0),
  c(1,0,0,1,1,0,0,0,1,1,0),
  c(0,1,1,0,0,0,1,1,0,0,1)
)
labels <- c("001", "NA", "run,three", "run four")
fixture <- function(mat = x, ids = paste0("run", seq_len(nrow(mat))),
                    k = "2", m = "4", blank_header = FALSE) {
  directory <- tempfile(pattern = "case ", tmpdir = work)
  dir.create(directory)
  input <- file.path(directory, "matrix input.csv")
  scores <- file.path(directory, "raw scores.csv")
  deviance <- file.path(directory, "separate fit summary.txt")
  write.csv(data.frame(datapoint_labels = ids, mat), input,
            row.names = FALSE, na = "")
  if (blank_header) {
    lines <- readLines(input)
    lines[1] <- sub('^"datapoint_labels"', '', lines[1])
    writeLines(lines, input)
  }
  list(input = input, scores = scores, deviance = deviance,
       args = c(input, scores, k, m, deviance), ids = ids, mat = mat)
}
invoke <- function(f, expected_error = NULL, arguments = f$args) {
  before <- tools::md5sum(f$input)
  # The subprocess runs inside Linux; shQuote protects file paths with spaces.
  output <- suppressWarnings(system2(
    file.path(R.home("bin"), "Rscript"),
    c("--vanilla", shQuote(c(source_file, arguments))),
    stdout = TRUE, stderr = TRUE, timeout = 90
  ))
  status <- attr(output, "status")
  if (is.null(status)) status <- 0L
  cat(paste(output, collapse = "\n"), "\n")
  cat("Wrapper exit status:", status, "\n")
  need(identical(before, tools::md5sum(f$input)), "The input CSV was modified")
  need(status != 124L, "The wrapper timed out; this is not an expected rejection")
  if (is.null(expected_error)) {
    need(status == 0L, "The valid-input fit failed")
    return(invisible(NULL))
  }
  need(status != 0L, "Invalid input unexpectedly succeeded")
  need(any(grepl(expected_error, output, fixed = TRUE)),
       paste("Missing expected error text:", expected_error))
  need(!file.exists(f$scores) && !file.exists(f$deviance),
       "A rejected fit left a scores or deviance output")
}
read_results <- function(f) {
  need(file.exists(f$scores) && file.exists(f$deviance), "A required output is missing")
  table <- read.csv(f$scores, row.names = NULL, colClasses = "character",
                    na.strings = character(), check.names = FALSE)
  need(identical(names(table), c("datapoint_labels", "PC1", "PC2")),
       "Unexpected scores CSV columns")
  need(nrow(table) == nrow(f$mat), "Wrong score-row count (no centroid belongs here)")
  need(identical(table$datapoint_labels, f$ids), "Run labels/order were not preserved")
  scores <- as.matrix(table[, c("PC1", "PC2"), drop = FALSE])
  storage.mode(scores) <- "double"
  need(all(is.finite(scores)), "Nonfinite score value")
  lines <- readLines(f$deviance)
  keys <- c("components", "m", "percent_deviance_explained")
  need(identical(sub(":.*$", "", lines), keys), "Unexpected fit-summary fields")
  values <- as.numeric(sub("^[^:]+: *", "", lines))
  need(all(is.finite(values)) && values[1] == 2 &&
       values[2] == as.numeric(f$args[4]), "Invalid summary values or wrong m/k")
  print(table, row.names = FALSE)
  cat(paste(lines, collapse = "\n"), "\n")
  list(scores = scores, percent = values[3])
}
fit <- function(f) {
  invoke(f)
  read_results(f)
}

baseline <- NULL
check("Reference fixture: m=4, geometry, deviance, labels and output schemas", function() {
  f <- fixture(ids = labels, blank_header = TRUE)
  result <- fit(f)
  # Reference score provenance is documented above the binary fixture.
  # Comparing distances permits one global orthogonal change of plotted axes,
  # but does not permit arbitrary sign changes on individual observations.
  expected <- cbind(
    c(4.96756989310632, -7.42875819587666, 12.7488840407735, -11.2979872320273),
    c(-7.80927209388169, 7.21294742051829, 1.711517188498, -5.51380214217161)
  )
  near(dist(result$scores), dist(expected), 1e-3, "Reference distances")
  # Convert the recorded m=4 proportion to a percentage.
  near(result$percent, 91.92537, 1e-3, "Reference deviance percentage")
  baseline <<- result
})
check("Repeatability in a fresh R process; named CSV label header", function() {
  need(!is.null(baseline), "Reference fixture did not pass")
  result <- fit(fixture(ids = labels))
  near(dist(result$scores), dist(baseline$scores), 1e-6, "Repeated distances")
  near(result$percent, baseline$percent, 1e-6, "Repeated deviance percentage")
})
check("Second known configuration: fixed m=6", function() {
  result <- fit(fixture(m = "6"))
  # Convert the recorded m=6 proportion to a percentage.
  near(result$percent, 97.6137532256003, 1e-3, "m=6 reference deviance percentage")
})
check("Boundary-sized valid input: three runs and three features", function() {
  fit(fixture(diag(3)))
})
check("Constant columns with otherwise informative data", function() {
  fit(fixture(cbind(x, 1, 0)))
})
check("Duplicate profiles retained when at least three distinct profiles exist", function() {
  result <- fit(fixture(rbind(x, x[1, , drop = FALSE])))
  near(result$scores[1, ], result$scores[5, ], 1e-6, "Identical-profile scores")
})
check("Finite positive fractional m", function() {
  fit(fixture(m = "4.5"))
})

check("Reject two runs before reaching the decomposition backend", function() {
  invoke(fixture(x[1:2, , drop = FALSE]), "at least 3 runs and 3 binary edge features")
})
for (count in 1:2) {
  check(paste("Reject", count, "feature column(s)"), function() {
    invoke(fixture(x[, seq_len(count), drop = FALSE]),
           "at least 3 runs and 3 binary edge features")
  })
}
check("Reject identical profiles instead of exporting infinite deviance", function() {
  invoke(fixture(matrix(1, nrow = 4, ncol = 5)), "at least 3 distinct")
})
check("Reject only two distinct profiles despite four runs", function() {
  invoke(fixture(x[c(1, 2, 1, 2), , drop = FALSE]), "at least 3 distinct")
})
check("Reject duplicate run identifiers", function() {
  invoke(fixture(ids = rep("same", 4)), "Run labels must be nonempty and unique")
})
check("Reject blank run identifiers", function() {
  invoke(fixture(ids = c(" ", "b", "c", "d")), "Run labels must be nonempty and unique")
})
for (value in c("1", "3", "2.9")) {
  check(paste("Reject k =", value), function() {
    invoke(fixture(k = value), "k must be exactly 2")
  })
}
for (value in c("0", "-1", "Inf", "bad")) {
  check(paste("Reject m =", value), function() {
    invoke(fixture(m = value), "m must be finite and positive")
  })
}
for (value in c("", "NA", "Inf", "bad", "2", "0.5")) {
  check(paste("Reject invalid feature value:", dQuote(value)), function() {
    mat <- x
    mat[1, 1] <- value
    invoke(fixture(mat), "Edge features must be complete, finite numeric zeros or ones")
  })
}
check("Reject old four-argument interface without producing outputs", function() {
  f <- fixture()
  invoke(f, "Usage:", f$args[1:4])
})

cat("\n=== RESULT:", passed, "passed;", failed, "failed ===\n")
unlink(work, recursive = TRUE)
quit(save = "no", status = if (failed == 0L) 0L else 1L)
'''


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--image", default="reedcompbio/lpca:v1",
                        help="Local image to test (default: reedcompbio/lpca:v1)")
    parser.add_argument("--log", type=Path,
                        help="Also save output to a new UTF-8 file; never overwrite")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Total container timeout in seconds (default: 600)")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    source = Path(__file__).resolve().with_name("run_lpca.R")
    if not source.is_file():
        parser.error("Place test_container.py beside run_lpca.R in docker-wrappers/LPCA")
    docker = shutil.which("docker")
    if docker is None:
        parser.error("Docker CLI was not found on PATH")

    env = os.environ.copy()
    env.update({"MSYS_NO_PATHCONV": "1", "MSYS2_ARG_CONV_EXCL": "*"})
    normalized_source = source.read_bytes().replace(b"\r\n", b"\n")
    expected_md5 = hashlib.md5(normalized_source, usedforsecurity=False).hexdigest()
    name = "spras-lpca-tests-" + uuid.uuid4().hex[:12]
    log_path = args.log.expanduser() if args.log is not None else None
    # Logging is optional; an existing file is never overwritten.
    log_context = (log_path.open("x", encoding="utf-8", newline="\n")
                   if log_path is not None else nullcontext(None))
    with log_context as log:
        def emit(text: str) -> None:
            if not text.endswith("\n"):
                text += "\n"
            print(text, end="", flush=True)
            if log is not None:
                log.write(text)
                log.flush()

        if log_path is not None:
            emit(f"Results log: {log_path}")
        emit(f"Local wrapper: {source}")
        emit(f"Local wrapper MD5 (LF normalized): {expected_md5}")
        try:
            inspected = subprocess.run(
                [docker, "image", "inspect", args.image], env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            if inspected.returncode:
                emit(inspected.stderr)
                emit("Image inspection failed. Build the selected image first; no image is pulled.")
                return 1
            image = json.loads(inspected.stdout)[0]
            emit(f"Image tag: {args.image}\nImage ID: {image['Id']}")
            emit(f"Image platform: {image.get('Os')} / {image.get('Architecture')}")
            # Run the inspected ID, not the mutable tag, to identify exactly what was tested.
            command = [docker, "run", "--name", name, "--rm", "--pull=never",
                       "--network=none", "-i", "--entrypoint", "Rscript",
                       image["Id"], "--vanilla", "/dev/stdin"]
            payload = f'expected_md5 <- "{expected_md5}"\n' + R_TESTS
            emit("Running container CLI tests. Their output is buffered until completion.")
            try:
                result = subprocess.run(
                    command, input=payload, env=env, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                    errors="replace", timeout=args.timeout,
                )
            finally:
                # On timeout/interrupt, remove only the uniquely named test container.
                # After an ordinary --rm exit, this is a harmless no-op.
                try:
                    subprocess.run([docker, "rm", "--force", name], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=30, check=False)
                except (OSError, subprocess.SubprocessError) as cleanup_error:
                    emit(f"WARNING: Could not confirm cleanup of {name}: {cleanup_error}")
            emit(result.stdout)
            emit(f"Container exit status: {result.returncode}")
            complete = "=== RESULT:" in result.stdout
            if not complete:
                emit("The test suite did not reach its summary; this run is not passing.")
            return 0 if result.returncode == 0 and complete else 1
        except subprocess.TimeoutExpired as exc:
            partial = exc.stdout or b""
            emit(partial.decode("utf-8", "replace") if isinstance(partial, bytes) else partial)
            emit(f"ERROR: Command timed out after {exc.timeout} seconds; the run is incomplete.")
            return 1
        except KeyboardInterrupt:
            emit("Interrupted; the run is incomplete.")
            return 130
        except (OSError, ValueError, KeyError, IndexError) as exc:
            emit(f"ERROR: {exc}")
            return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileExistsError as exc:
        print(f"ERROR: Log already exists: {exc.filename}\n"
              "Choose a different --log path, or omit --log for terminal output only.",
              file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
