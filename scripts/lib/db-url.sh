#!/usr/bin/env bash

DEFAULT_DATABASE_URL="postgresql+psycopg://prompteer:prompteer@localhost:55432/prompteer"

to_pg_url() {
  local url="${1:-$DEFAULT_DATABASE_URL}"
  case "$url" in
    postgresql+psycopg://*) printf 'postgresql://%s\n' "${url#postgresql+psycopg://}" ;;
    postgresql+psycopg2://*) printf 'postgresql://%s\n' "${url#postgresql+psycopg2://}" ;;
    postgresql+asyncpg://*) printf 'postgresql://%s\n' "${url#postgresql+asyncpg://}" ;;
    postgres+psycopg://*) printf 'postgresql://%s\n' "${url#postgres+psycopg://}" ;;
    postgres://*) printf 'postgresql://%s\n' "${url#postgres://}" ;;
    *) printf '%s\n' "$url" ;;
  esac
}

to_sqlalchemy_url() {
  local url="${1:-$DEFAULT_DATABASE_URL}"
  case "$url" in
    postgresql+psycopg://* | postgresql+psycopg2://* | postgresql+asyncpg://*)
      printf '%s\n' "$url"
      ;;
    postgresql://*) printf 'postgresql+psycopg://%s\n' "${url#postgresql://}" ;;
    postgres://*) printf 'postgresql+psycopg://%s\n' "${url#postgres://}" ;;
    *) printf '%s\n' "$url" ;;
  esac
}

database_name_from_url() {
  local url="${1%%\?*}"
  url="${url%/}"

  local database_name="${url##*/}"
  if [[ -z "$database_name" || "$database_name" == "$url" || "$database_name" == *":"* ]]; then
    return 1
  fi

  printf '%s\n' "$database_name"
}

maintenance_url_from_url() {
  local url="$1"
  local query=""

  if [[ "$url" == *\?* ]]; then
    query="?${url#*\?}"
    url="${url%%\?*}"
  fi

  url="${url%/}"
  printf '%s/postgres%s\n' "${url%/*}" "$query"
}

database_url_with_name() {
  local url="$1"
  local database_name="$2"
  local query=""

  if [[ "$url" == *\?* ]]; then
    query="?${url#*\?}"
    url="${url%%\?*}"
  fi

  url="${url%/}"
  printf '%s/%s%s\n' "${url%/*}" "$database_name" "$query"
}
