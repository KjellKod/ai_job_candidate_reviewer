# Getting Started

Audience: New users who want results in minutes.

## 60‑Second Quickstart

```bash
# 1) Install
pip3 install -r requirements.txt

# 2) Configure API key
echo "OPENAI_API_KEY=sk-proj-your-key" > .env

# 3) Prepare job files
mkdir -p data/intake
# Put job_description.pdf (required) into data/intake/
# Put ideal_candidate.txt (recommended) into data/intake
# Put warning_flags.txt (recommended) into data/intake

# 4) Setup job, this will ingest the job description, what an ideal candidate is and some warning flags you want our screening to look out for. 
python3 candidate_reviewer.py setup-job "software_engineer"

# 5) Add candidates to data/intake/
# e.g., resume_john_doe.pdf, application_john_doe.txt

# 6) Process and review
python3 candidate_reviewer.py process-candidates "software_engineer"
python3 candidate_reviewer.py show-candidates "software_engineer"
```

## What You’ll See
- Ranked candidates with scores, recommendation, interview priority
- CSV and HTML reports generated under `data/output/{job}`

## Next Steps (2 mins)
- Provide feedback to teach the AI:
  ```bash
  python3 candidate_reviewer.py provide-feedback "software_engineer" "john_doe"
  python3 candidate_reviewer.py provide-feedback "software_engineer" 1 #where john doe has the list id of '1'
  
  ```
- Re-evaluate with insights (auto-suggested every 2 feedbacks):
  ```bash
  python3 candidate_reviewer.py re-evaluate "software_engineer"  # all of them 
  python3 candidate_reviewer.py re-evaluate "software_engineer" -c john_doe # just joe
   python3 candidate_reviewer.py re-evaluate "software_engineer" -c "John Doe" # just joe
  ```
- Add screening filters (hard rules) during feedback to auto-reject/mute mismatches

## Where Things Go
```
data/
├── intake/                 # drop files here
├── jobs/{job}/             # job description, ideal_candidate, flags
├── candidates/{job}/{name}/
└── output/{job}/           # CSV, HTML
```

## Learn the System (skim)
- Screening filters (candidate 'must‑have qualities' rules): see [SCREENING_FILTERS.md](SCREENING_FILTERS.md)
- How rankings + filters work: see “How It Works” in [README.md](README.md)
- Architecture overview (one screen): see [ARCHITECTURE.md](ARCHITECTURE.md)

## Feature Highlights
- Feedback → insights every 2 feedbacks → re‑evaluate with improvements
- Screening filters: `set_recommendation`, `cap_recommendation`, `deduct_points`
- Duplicate detection: identity‑based matching (email, phone, LinkedIn, GitHub)

## Troubleshooting
- Test API connectivity: `python3 candidate_reviewer.py test-connection`
- List jobs: `python3 candidate_reviewer.py list-jobs`
- Open latest HTML report: `python3 candidate_reviewer.py open-reports "software_engineer"`
