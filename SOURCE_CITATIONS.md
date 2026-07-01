# Source Citations

This release is derived from aggregate U.S. government source files. No person-level source rows are included in the public release.

## Included v0.1.0 Sources

### `census_2020_first_names_by_sex`

- Source organization: U.S. Census Bureau
- Source title: Frequently Occurring First Names in the 2020 Census by Sex
- Landing page identifier: https://www.census.gov/topics/population/genealogy/data/2020_names.html
- File identifier: https://www2.census.gov/topics/genealogy/2020surnames/Names2020_FirstNames_Sex.xlsx
- Local file name: `Names2020_FirstNames_Sex.xlsx`
- Local source ID: `census_2020_first_names_by_sex`
- Used fields: name only
- Excluded fields: counts, sex, race, Hispanic origin, geography

Suggested citation:

```text
U.S. Census Bureau. (2026, April 14). Frequently Occurring First Names in the 2020 Census by Sex [Data set]. U.S. Department of Commerce. https://www.census.gov/topics/population/genealogy/data/2020_names.html
```

### `census_2020_last_names_race_hispanic`

- Source organization: U.S. Census Bureau
- Source title: Frequently Occurring Last Names in the 2020 Census by Race and Hispanic Origin
- Landing page identifier: https://www.census.gov/topics/population/genealogy/data/2020_names.html
- File identifier: https://www2.census.gov/topics/genealogy/2020surnames/Names2020_LastNames_RaceHispanic.xlsx
- Local file name: `Names2020_LastNames_RaceHispanic.xlsx`
- Local source ID: `census_2020_last_names_race_hispanic`
- Used fields: name only
- Excluded fields: counts, race, Hispanic origin, geography

Suggested citation:

```text
U.S. Census Bureau. (2026, April 14). Frequently Occurring Last Names in the 2020 Census by Race and Hispanic Origin [Data set]. U.S. Department of Commerce. https://www.census.gov/topics/population/genealogy/data/2020_names.html
```

### `census_2010_surnames`

- Source organization: U.S. Census Bureau
- Source title: Frequently Occurring Surnames from the 2010 Census
- Landing page identifier: https://www.census.gov/topics/population/genealogy/data/2010_surnames.html
- File identifier: https://www2.census.gov/topics/genealogy/2010surnames/names.zip
- Local file name: `census_2010_surnames.zip`
- Local source ID: `census_2010_surnames`
- Used fields: name only
- Excluded fields: counts, rank, proportion, race, Hispanic origin

Suggested citation:

```text
U.S. Census Bureau. (2021, October 8). Frequently Occurring Surnames from the 2010 Census [Data set]. U.S. Department of Commerce. https://www.census.gov/topics/population/genealogy/data/2010_surnames.html
```

### `ssa_national_baby_names`

- Source organization: U.S. Social Security Administration
- Source title: Popular Baby Names, National Data
- Landing page identifier: https://www.ssa.gov/oact/babynames/limits.html
- File identifier: https://www.ssa.gov/oact/babynames/names.zip
- Local file name: `ssa_names_national.zip`
- Local source ID: `ssa_national_baby_names`
- Used fields: name only
- Excluded fields: birth year, sex, counts
- v0.1.0 local handling: supplied from a local extracted copy of the official SSA national names ZIP because the SSA endpoint blocked automated download in this environment

Suggested citation:

```text
U.S. Social Security Administration. (n.d.). Popular Baby Names: National Data [Data set]. https://www.ssa.gov/oact/babynames/limits.html
```

## Notes

- The local source IDs are project identifiers, not globally registered persistent identifiers.
- The source landing pages and direct file URLs are the best available upstream identifiers for these aggregate government data files.
- If a source later receives a DOI or other persistent identifier, update this file, `.zenodo.json`, and release notes before publishing the next release.
