"""Convert raw HN comments to a documented, reusable dataset."""
import json
import re
from pathlib import Path
from html import unescape
import pandas as pd

SKILLS = ['python', 'java', 'javascript', 'typescript', 'react', 'node.js', 'sql', 'postgresql', 'aws', 'docker', 'kubernetes', 'go', 'rust', 'c++', 'ruby', 'rails', 'tensorflow', 'pytorch', 'machine learning', 'llm', 'generative ai', 'git', 'linux', 'scala', 'swift', 'flutter']
PATTERNS = {s: re.compile(r'(?<![\w])' + re.escape(s) + r'(?![\w])', re.I) for s in SKILLS}

def strip_html(value):
    value = re.sub(r'<[^>]+>', ' ', value or '')
    return re.sub(r'\s+', ' ', unescape(value)).strip()

def clean(source='data/raw/hn_jobs.jsonl', dest='data/processed/jobs_cleaned.csv'):
    records = []
    for line in Path(source).read_text(encoding='utf-8').splitlines():
        obj = json.loads(line)
        content = strip_html(obj.get('text'))
        if len(content) < 30:
            continue
        first = content.split('|', 1)
        date = pd.to_datetime(obj.get('created_at'), utc=True, errors='coerce')
        records.append({'id': obj['id'], 'thread_id': obj['thread_id'], 'date': date, 'year': date.year if pd.notna(date) else None, 'month': date.month if pd.notna(date) else None, 'company': first[0].strip() if len(first) > 1 else None, 'role': None, 'location': None, 'remote': bool(re.search(r'\bremote\b', content, re.I)), 'salary': None, 'skills': ', '.join(s for s,p in PATTERNS.items() if p.search(content)), 'text': content})
    df = pd.DataFrame.from_records(records)
    if df.empty:
        raise ValueError('No records found; inspect the collection results first.')
    df = df.drop_duplicates(subset=['id']).sort_values('date')
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    print(f'Saved {len(df):,} unique posts to {dest}')
    print('Date range:', df.date.min(), 'to', df.date.max())
    print('Missing values:\n', df.isna().sum())

if __name__ == '__main__':
    clean()
