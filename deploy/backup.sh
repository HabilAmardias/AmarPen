#!/usr/bin/env sh
set -eu

: "${BACKUP_DIR:=./backups}"
: "${POSTGRES_CONTAINER:=ai-assisted-pentest-db-1}"
: "${S3_CONTAINER:=ai-assisted-pentest-s3-1}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${BACKUP_DIR}/${timestamp}"
mkdir -p "${target}"

docker exec "${POSTGRES_CONTAINER}" pg_dump -U pentest -d pentest -Fc > "${target}/database.dump"
docker exec "${S3_CONTAINER}" sh -c "tar -C /var/lib/localstack -cf - ." | tar -C "${target}" -xf -
printf '%s\n' "${timestamp}" > "${target}/manifest.txt"

echo "Backup written to ${target}"
