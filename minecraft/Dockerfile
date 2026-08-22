# Ships BDS's runtime dependencies only — no game files are baked in.
# The backend creates a container from this image per server it manages,
# passing `working_dir=/servers/<server-id>` and `user=<BEDROCK_UID>:
# <BEDROCK_GID>` at creation time (see backend/app/docker_utils.py's
# create_minecraft_container) rather than baking a single fixed
# directory into the image — that's what lets one image serve any
# number of independently-managed servers sharing one volume.
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
    && useradd -m -u ${BEDROCK_UID} -g ${BEDROCK_GID} bedrock

# `exec` replaces the shell as PID 1 so `docker stop` (SIGTERM) reaches
# bedrock_server directly instead of being swallowed by bash — without
# this the server can't save the world on shutdown and every stop turns
# into a hard kill after the compose stop-grace-period. The working
# directory (and therefore where `./bedrock_server` resolves to) is set
# per-container at creation time, not here.
CMD ["bash", "-c", "chmod +x ./bedrock_server 2>/dev/null; LD_LIBRARY_PATH=. exec ./bedrock_server"]
