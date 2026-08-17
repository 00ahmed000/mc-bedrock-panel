# Ships BDS's runtime dependencies only — the actual bedrock_server binary
# and game files are delivered into the bedrock_data volume by the panel's
# "Update Server" action, never baked into this image, per Mojang's
# distribution terms.
FROM ubuntu:22.04

ARG BEDROCK_UID=1000
ARG BEDROCK_GID=1000

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libcurl4 \
        ca-certificates \
        openssl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g ${BEDROCK_GID} bedrock \
    && useradd -m -u ${BEDROCK_UID} -g ${BEDROCK_GID} bedrock \
    && mkdir -p /bedrock \
    && chown ${BEDROCK_UID}:${BEDROCK_GID} /bedrock

WORKDIR /bedrock

# `exec` replaces the shell as PID 1 so `docker stop` (SIGTERM) reaches
# bedrock_server directly instead of being swallowed by bash — without
# this the server can't save the world on shutdown and every stop turns
# into a hard kill after the compose stop-grace-period.
CMD ["bash", "-c", "chmod +x ./bedrock_server 2>/dev/null; LD_LIBRARY_PATH=. exec ./bedrock_server"]
