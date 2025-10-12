# AI Job Candidate Reviewer

Recruiting at scale is hard — it's time-consuming, subjective, and inconsistent.
The AI Job Candidate Reviewer helps teams automate first-pass resume screening while keeping humans firmly in control.

Simply drop resumes and job descriptions into organized folders, and receive AI-generated candidate rankings with detailed notes and scores. The system learns from your feedback to refine its screening accuracy over time.

**🤖 Powered by GPT-5** (with intelligent fallback to GPT-4/GPT-4-turbo). The CLI prints the model used for every AI-related command.

```
Candidate → AI Evaluation → Human Feedback → AI Learning → Improved Evaluations
```

How It Helps
   •  Quickly identify top candidates with consistent, structured evaluations
   •  Reduce manual effort without losing human judgment
   •  Adapt the AI’s ranking logic to your hiring patterns
   •  Reuse screening context for future, similar positions


⚠️ Important Note
The AI reviewer assists in ranking candidates but is not a decision maker.
Always review AI-generated evaluations before making hiring decisions.
The system improves through human feedback and builds reusable screening context across similar roles.



## Quick Start

```bash
# 1. Install and setup environment
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OpenAI API key

# 2. Test connection
python3 candidate_reviewer.py test-connection

# 3. Setup job (once per position)
# Drop files into data/intake/:
# - job_description.pdf (required)
# - ideal_candidate.txt (optional) 
# - warning_flags.txt (optional)
python3 candidate_reviewer.py setup-job "mobile_engineer"

# Update an existing job context later (refresh ideal/warnings)
python3 candidate_reviewer.py setup-job "mobile_engineer" --update

# 4. Add candidates (ongoing)
# Drop files into data/intake/:
# - resume_firstname_lastname.pdf (required)
# - coverletter_firstname_lastname.pdf (optional)
# - application_firstname_lastname.txt (optional)
python3 candidate_reviewer.py process-candidates "mobile_engineer"

# 5. Review and rank candidates
python3 candidate_reviewer.py show-candidates "mobile_engineer"

# 6. Provide feedback to improve AI
python3 candidate_reviewer.py provide-feedback "mobile_engineer" "candidate_name" "feedback text"

# 7. Re-evaluate with improved AI
python3 candidate_reviewer.py re-evaluate "mobile_engineer"

# 8. View detailed reports
python3 candidate_reviewer.py open-reports "mobile_engineer"
```

- ✅ **Super simple** - just rename files and drop them
- ✅ **No complex commands** - no file path arguments
- ✅ **Less errors** - can't typo file paths


## File Organization

**1. Drop files here:**

Example for `--setup-job` 
```
data/intake/
├── job_description.pdf              # Required for --setup-job
├── ideal_candidate.txt              # Optional for --setup-job  
├── warning_flags.txt                # Optional for --setup-job

```
Example for `--process_candidates`
```
data/intake/
├── resume_john_doe.pdf              # Required for --process-candidates
├── coverletter_john_doe.pdf         # Optional for --process-candidates
└── application_john_doe.txt         # Optional for --process-candidates
...
├── resume_jane_doe.pdf              # Required for --process-candidates
└── application_jane_doe.txt         # Optional for --process-candidates
...
```



**2. After processing, files are organized into:**
```
data/
├── jobs/                           # Processed job info
│   └── {job_name}/
│       ├── job_description.pdf
│       ├── ideal_candidate.txt
│       └── warning_flags.txt
├── candidates/                     # Processed candidates  
│   └── {job_name}/
│       ├── john_doe/
│       │   ├── resume.pdf
│       │   ├── cover_letter.pdf
│       │   └── review.json
│       └── jane_smith/
│           ├── resume.pdf
│           └── application.txt
└── output/                        # Results
    └── {job_name}/
        ├── candidate_scores.csv    # 👈 Main review file
        ├── summary_report.html
        └── detailed_reviews/
```

Notes:
- Job setup files are moved from `data/intake/` into `data/jobs/{job_name}/` during setup, keeping intake clean.
- Candidate files are copied into their candidate directories and the originals in intake are cleaned up after successful processing.
- If a candidate is missing required files, processing stops at that candidate with a clear error so you can fix/remove and retry.

## All Commands

### **Core Workflow:**
```bash
python3 candidate_reviewer.py setup-job "job_name"           # Setup job from intake files
python3 candidate_reviewer.py process-candidates "job_name"  # Process candidates from intake
python3 candidate_reviewer.py show-candidates "job_name"     # Show ranked results
```

Options:
- setup-job
  - `-j, --job-description PATH`  Use a specific job description file
  - `-i, --ideal-candidate PATH`  Use a specific ideal-candidate file (optional)
  - `-w, --warning-flags PATH`    Use a specific warning-flags file (optional)
  - `--update/--no-update`        Update an existing job setup (default: no-update)

- process-candidates
  - `-r, --resume PATH`           Process a single candidate by file path
  - `-c, --cover-letter PATH`     Optional cover letter path
  - `-a, --application PATH`      Optional application/questionnaire path
  - `-n, --candidate-name TEXT`   Candidate name (required with -r)

- show-candidates: no options

### **Feedback & Learning:**
```bash
python3 candidate_reviewer.py provide-feedback "job_name" "candidate_name" "feedback text"
python3 candidate_reviewer.py show-insights "job_name"       # View AI learning
python3 candidate_reviewer.py re-evaluate "job_name"         # Re-evaluate with insights
```

Options:
- provide-feedback: no options (feedback text optional; if omitted, prompts interactively)
- show-insights: no options
- re-evaluate
  - `-c, --candidates TEXT`       Specify one or more candidates (repeatable)

### **Reports & Analysis:**
```bash
python3 candidate_reviewer.py open-reports "job_name"        # Open HTML report in browser
python3 candidate_reviewer.py list-reports "job_name"        # List all available reports
```

Options:
- open-reports: no options
- list-reports: no options

### **System Management:**
```bash
python3 candidate_reviewer.py test-connection                # Test API connection
python3 candidate_reviewer.py list-models                    # Show available AI models
python3 candidate_reviewer.py list-jobs                      # Show all jobs
python3 candidate_reviewer.py --help                         # Show all commands
```

Options:
- test-connection: no options
- list-models: no options
- list-jobs: no options

## Results

**CSV Format:** Open `candidate_scores.csv` in Excel with:
- **Overall Score** (0-100)
- **Recommendation** (STRONG_YES, YES, MAYBE, NO, STRONG_NO)
- **Key Strengths** and **Concerns**
- **Interview Priority** (HIGH, MEDIUM, LOW)

**Terminal Ranking:** Use `--show_candidates` for quick command-line view:
```
Job: senior_python_dev_2024

1. john_doe - STRONG_YES (Score: 87)
   ✅ Expert Python dev, 6yrs experience, strong portfolio
   
2. mike_smith - YES (Score: 72) 
   ✅ Good technical skills, solid experience
   ⚠️ Limited leadership experience

3. jane_wilson - MAYBE (Score: 58)
   ✅ Strong communication, eager to learn  
   ⚠️ No Python experience, career change

4. bob_jones - NO (Score: 34)
   ❌ No relevant experience, poor communication
```

**This shows users both output options:**
- **CSV** for detailed spreadsheet analysis
- **Terminal ranking** for quick command-line review
7
## File Naming

**Job files:** Any names work, script auto-detects
**Candidate files:** Include name in filename
- `resume_john_doe.pdf` → Candidate: "john_doe"
- `JohnDoe_CV.pdf` → Candidate: "johndoe"

## Optional: Improve Results

Create a file that explains the ideal candidate: `ideal_candidate.txt`:
```
• 5+ years Python experience
• Strong communication skills
• AWS/cloud experience preferred
• Team leadership or mentoring experience
• Bachelor's degree in Computer Science or equivalent

Questionnaire responses should show:
• Specific examples with measurable results
• Clear problem-solving thought process
• Enthusiasm for the role and company
• Understanding of our tech stack
• Realistic timeline estimates for projects
```

Create `warning_flags.txt`:
```
• Job hopping (3+ jobs in 2 years)
• No relevant programming experience
• Poor written communication

Questionnaire red flags:
• Vague answers without specific examples
• Copy-pasted responses from other applications
• Unrealistic claims or timelines
• Negative attitude toward previous employers
• Avoiding technical questions
```

This way the AI can evaluate both the resume/cover letter AND the questionnaire responses using your specific criteria. It helps catch candidates who look good on paper but give poor application answers, or vice versa.

## Troubleshooting

- **Missing API key:** Add `OPENAI_API_KEY` to `.env` file
- **No job description:** Drop a PDF into `data/intake/jobs/`
- **No candidates:** Drop resumes into `data/intake/candidates/`
- **Multiple PDFs:** Script will ask which job description to use

Get API key: https://platform.openai.com/api-keys




