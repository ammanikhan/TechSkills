"""Collect Hacker News Who is Hiring top-level comments via public Algolia API."""
import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timezone
import requests

API = 'https://hn.algolia.com/api/v1/search_by_date'

def collect(start_year=2023, end_year=2026, output='data/raw/hn_jobs.jsonl'):
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with dest.open('w', encoding='utf-8') as f:
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                if (year, month) > (datetime.now(timezone.utc).year, datetime.now(timezone.utc).month):
                    continue
                date_from = datetime(year, month, 1, tzinfo=timezone.utc)
                date_to = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=timezone.utc)
                # Find the monthly thread using its title; verify results rather than assuming a fixed ID.
                params = {'query': 'Ask HN: Who is hiring?', 'tags': 'story', 'numericFilters': f'created_at_i>={int(date_from.timestamp())},created_at_i<{int(date_to.timestamp())}', 'hitsPerPage': 100}
                stories = requests.get(API, params=params, timeout=30).json().get('hits', [])
                threads = [s for s in stories if (s.get('title') or '').lower().startswith('ask hn: who is hiring?')]
                for thread in threads:
                    page = 0
                    while True:
                        params = {'tags': f'comment,story_{thread["objectID"]}', 'hitsPerPage': 100, 'page': page}
                        response = requests.get(API, params=params, timeout=30)
                        response.raise_for_status()
                        payload = response.json()
                        for hit in payload.get('hits', []):
                            if str(hit.get('parent_id')) != str(thread['objectID']):
                                continue
                            f.write(json.dumps({'id': hit.get('objectID'), 'thread_id': thread['objectID'], 'created_at': hit.get('created_at'), 'text': hit.get('comment_text') or ''}, ensure_ascii=False) + '\n')
                            count += 1
                        page += 1
                        if page >= payload.get('nbPages', 0):
                            break
                        time.sleep(0.15)
                print(f'{year}-{month:02d}: {len(threads)} thread(s), {count} total posts')
    print(f'Saved {count} raw posts to {dest}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-year', type=int, default=2023)
    parser.add_argument('--end-year', type=int, default=2026)
    args = parser.parse_args()
    collect(args.start_year, args.end_year)
