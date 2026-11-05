#!/usr/bin/env sh
set -eu

: "${1:?Usage: restore.sh <backup-directory>}"
: "${POSTGRES_CONTAINER:=ai-assisted-pentest-db-1}"
: "${S3_CONTAINER:=ai-assisted-pentest-s3-1}"
source_dir="$1"

test -f "${source_dir}/database.dump" || { echo "database.dump missing"; exit 1; }

docker exec -i "${POSTGRES_CONTAINER}" pg_restore -U pentest -d pentest --clean --if-exists < "${source_dir}/database.dump"
tar -C "${source_dir}" --exclude manifest.txt --exclude database.dump -cf - . | docker exec -i "${S3_CONTAINER}" tar -C /var/lib/localstack -xf -

echo "Restore complete. Reconcile run authority and evidence references before resuming execution."
