# AI Job Candidate Reviewer

Recruiting at scale is hard — it’s time-consuming, subjective, and inconsistent.
The AI Job Candidate Reviewer helps teams automate first-pass resume screening while keeping humans firmly in control.

Simply drop resumes and job descriptions into organized folders, and receive AI-generated candidate rankings with detailed notes and scores in a CSV you can open in Excel or Google Sheets.

The system learns from your feedback to refine its screening accuracy over time — building reusable context for similar roles and ensuring the process continuously improves.


```
Candidate → AI Score → Human Feedback → Model Recalibration → Updated Ranking
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
echo "OPENAI_API_KEY=your_key_here" > .env

# 2. Setup job (once per position)
# Drop files into data/intake/jobs/ with standard names:
# - job_description.pdf (required)
# - ideal_candidate.txt (optional) 
# - warning_flags.txt (optional)
python candidate_reviewer.py --setup-job "job_name"

# 2. Add candidates (ongoing)
# Drop files into data/intake/candidates/ with pattern:
# - resume_firstname_lastname.pdf (required)
# - coverletter_firstname_lastname.pdf (optional)
# - application_firstname_lastname.txt (optional)
python candidate_reviewer.py --process-candidates "job_name"

# 4. Review and rank candidates
python candidate_reviewer.py --show_candidates "job_name"     # Quick ranking view
# OR open data/output/job_name/candidate_scores.csv in Excel  # Detailed spreadsheet


# Other useful commands
python candidate_reviewer.py --list-jobs                     # Show all jobs
python candidate_reviewer.py --test-connection               # Test OpenAI API
python candidate_reviewer.py --help                          # Show all options
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

## Usage

```bash
# Once per job: Job setup
python candidate_reviewer.py --setup-job "job_name"

# Whenever : Process candidates
python candidate_reviewer.py --process-candidates "job_name"

# Whenever: List available jobs
python candidate_reviewer.py --list-jobs

# Whenever: List in ranked order the candidates
python candidate_reviewer.py --show_candidates "job_name"
```

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




