#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/raw/census data/raw/ssa

download() {
  local url="$1"
  local out="$2"
  if [[ -f "$out" ]]; then
    echo "exists: $out"
    return 0
  fi
  echo "download: $url -> $out"
  curl -L --fail --retry 3 --retry-delay 2 "$url" -o "$out"
}

download "https://www2.census.gov/topics/genealogy/2020surnames/Names2020_FirstNames_Sex.xlsx" "data/raw/census/Names2020_FirstNames_Sex.xlsx"
download "https://www2.census.gov/topics/genealogy/2020surnames/Names2020_LastNames_RaceHispanic.xlsx" "data/raw/census/Names2020_LastNames_RaceHispanic.xlsx"
download "https://www2.census.gov/topics/genealogy/2010surnames/names.zip" "data/raw/census/2010_names.zip"
download "https://www2.census.gov/topics/genealogy/2000surnames/names.zip" "data/raw/census/2000_names.zip"
download "https://www.ssa.gov/oact/babynames/names.zip" "data/raw/ssa/names.zip"
download "https://www.ssa.gov/oact/babynames/state/namesbystate.zip" "data/raw/ssa/namesbystate.zip"
download "https://www.ssa.gov/oact/babynames/territory/namesbyterritory.zip" "data/raw/ssa/namesbyterritory.zip"
