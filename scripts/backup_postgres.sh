#!/bin/sh
set -eu

: "${PGHOST:?PGHOST is required}"
: "${PGDATABASE:?PGDATABASE is required}"
: "${PGUSER:?PGUSER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"

BACKUP_DIRECTORY="${BACKUP_DIRECTORY:-/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DESTINATION="${BACKUP_DIRECTORY}/${PGDATABASE}_${TIMESTAMP}.dump"
TEMPORARY="${DESTINATION}.partial"

mkdir -p "${BACKUP_DIRECTORY}"
trap 'rm -f "${TEMPORARY}"' EXIT INT TERM

pg_dump \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="${TEMPORARY}" \
  "${PGDATABASE}"

mv "${TEMPORARY}" "${DESTINATION}"
find "${BACKUP_DIRECTORY}" -type f -name "${PGDATABASE}_*.dump" \
  -mtime "+${BACKUP_RETENTION_DAYS}" -delete

printf 'Database backup created: %s\n' "${DESTINATION}"
