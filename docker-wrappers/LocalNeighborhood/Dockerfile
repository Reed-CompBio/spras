# Stage 1: The Builder Stage (Do not delete this!)
FROM python:3.12-alpine AS builder

RUN apk add --no-cache build-base gcc musl-dev

WORKDIR /build

COPY pyproject.toml MANIFEST.in README.md LICENSE ./
COPY spras ./spras

RUN pip install --no-cache-dir --user -e .

# Stage 2: The Runtime Stage
FROM python:3.12-alpine

WORKDIR /data

# This now successfully copies from Stage 1 above
COPY --from=builder /root/.local /root/.local

COPY docker-wrappers/LocalNeighborhood/local_neighborhood_alg.py /data/

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "spras.localneighborhood"]
