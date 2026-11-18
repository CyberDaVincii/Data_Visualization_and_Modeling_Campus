"""Prepare the arXiv abstract sample used in Investigation 2 of the text lab.

Run from the week04/lab folder:  python data/fetch_arxiv_sample.py

1. Queries the arXiv API (https://info.arxiv.org/help/api/) for every paper listed in cs.AI
   (primary or cross-listed) whose first version was submitted in October 2019, 2021, 2023, or 2025.
2. Saves the IDs of that full population to data/arxiv_cs_ai_october_population_ids.csv.
3. Draws a fixed random sample of 300 papers per year (random_state=42) and saves it to
   data/arxiv_cs_ai_abstracts_2019_2025.csv.

The saved files were produced on November 17, 2026. arXiv metadata can change when authors post new
versions, so running this again later may return slightly different abstracts. The analysis reads the
saved files, not the live API.
"""
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

DATA_DIR = Path('data')
YEARS = [2019, 2021, 2023, 2025]
PAGE_SIZE = 2000
SAMPLE_PER_YEAR = 300
SEED = 42
NS = {'a': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom',
      'os': 'http://a9.com/-/spec/opensearch/1.1/'}


def fetch_year(year):
    """Return one dict per paper listed in cs.AI and first submitted in October of the year."""
    rows, seen, start, total = [], set(), 0, None
    while total is None or start < total:
        url = ('https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+submittedDate:'
               f'%5B{year}10010000+TO+{year}10312359%5D&sortBy=submittedDate&sortOrder=ascending'
               f'&start={start}&max_results={PAGE_SIZE}')
        for _ in range(5):
            time.sleep(4)  # arXiv asks for at least 3 seconds between requests
            root = ET.fromstring(urllib.request.urlopen(url, timeout=120).read())
            entries = root.findall('a:entry', NS)
            total = int(root.find('os:totalResults', NS).text)
            if len(entries) == min(PAGE_SIZE, total - start):
                break
        else:
            raise RuntimeError(f'Incomplete page for {year} starting at {start}')
        for entry in entries:
            arxiv_id = entry.find('a:id', NS).text.rsplit('/abs/', 1)[1].rsplit('v', 1)[0]
            if arxiv_id in seen:
                continue
            seen.add(arxiv_id)
            rows.append({
                'arxiv_id': arxiv_id,
                'year': year,
                'submitted': entry.find('a:published', NS).text,
                'title': ' '.join(entry.find('a:title', NS).text.split()),
                'abstract': ' '.join(entry.find('a:summary', NS).text.split()),
                'primary_category': entry.find('arxiv:primary_category', NS).get('term'),
                'categories': ' '.join(c.get('term') for c in entry.findall('a:category', NS)),
            })
        start += PAGE_SIZE
    return rows


def draw_sample(population_df):
    """Fixed random sample of SAMPLE_PER_YEAR papers per year, ordered by submission time."""
    return (population_df.groupby('year', group_keys=False)
            .sample(n=SAMPLE_PER_YEAR, random_state=SEED)
            .sort_values(['year', 'submitted'])
            .reset_index(drop=True))


if __name__ == '__main__':
    population_df = pd.DataFrame([row for year in YEARS for row in fetch_year(year)])
    population_df[['arxiv_id', 'year']].to_csv(DATA_DIR / 'arxiv_cs_ai_october_population_ids.csv', index=False)
    draw_sample(population_df).to_csv(DATA_DIR / 'arxiv_cs_ai_abstracts_2019_2025.csv', index=False, encoding='utf-8')
    print(population_df.groupby('year').size())
