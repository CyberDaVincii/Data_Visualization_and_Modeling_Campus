# Census Business Trends and Outlook Survey, sector file

- **File:** `census_btos_sector_2026-11-17.xlsx` (the Census download `Sector.xlsx`, unchanged apart from the file name)
- **Title:** Business Trends and Outlook Survey (BTOS), estimates by sector
- **Publisher:** U.S. Census Bureau
- **Source URL:** https://www.census.gov/hfp/btos/downloads/Sector.xlsx (data page: https://www.census.gov/hfp/btos/data_downloads)
- **Access date:** November 17, 2026 (the file on the server was last modified November 3, 2026)
- **Reuse terms:** U.S. government work, in the public domain. Cite the Census Bureau as the source.
- **Coverage:** Two-week survey cycles from September 2023 through the cycle with reference period October 5 to October 18, 2026. The AI questions used here appear in this file from the cycle with reference period November 3 to November 16, 2025 onward (25 cycles).

## Sheets used

| Sheet | What it holds |
| --- | --- |
| `Response Estimates` | One row per sector, question, and answer. One column per survey cycle (`YYYYFF`: ISO year and two-week cycle number). Values are text percentages such as `45.0%`. |
| `Response Standard Errors` | Same layout, holding the standard error of each estimate in percentage points. |
| `Collection and Reference Dates` | Collection and reference dates for each cycle code (`Smpdt`). |

## Features used by the dashboard

| Feature | Meaning and codes |
| --- | --- |
| `Sector` | Two-digit NAICS 2022 sector code. Manufacturing is reported as 31, retail trade as 44, and transportation and warehousing as 48. `XX` (multi-unit companies operating in several sectors) is not an industry and is not used. |
| `Question ID` 7 | "In the last two weeks, did this business use Super Intelligence or SI (formerly referred to as Artificial Intelligence or AI) in any of its business functions?" |
| `Question ID` 28 | "During the next six months, do you think this business will be using Super Intelligence or SI (formerly referred to as Artificial Intelligence or AI) in any of its business functions?" |
| `Answer` | Only the `Yes` rows are used. The value is the estimated percent of businesses in the sector that answered Yes. |
| Cycle columns | `S` means Census suppressed the estimate. `.` means the question was not asked in that cycle. |

Sectors 11 (agriculture, forestry, fishing) and 55 (management of companies) are left out because Census suppressed their AI use estimate in more than half of the 25 cycles.
