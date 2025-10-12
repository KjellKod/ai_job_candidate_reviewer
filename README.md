# 🤖 AI Job Candidate Reviewer

> **Stop spending hours manually screening resumes. Let AI do the first pass.**

Transform your hiring workflow with AI-powered resume screening that's fast, consistent, and adapts to your preferences.

## 🎯 Why This Matters

Recruiting at scale is **painful**:
- ⏰ **Time-consuming** - Hours spent reading similar resumes
- 🎲 **Inconsistent** - Different standards across reviewers or days
- 😓 **Draining** - Mental fatigue from repetitive evaluation

**This tool changes that:**

✨ **Drop files, get rankings** - No complex setup, just organized folders  
🎯 **Consistent evaluations** - Same criteria applied to every candidate  
📊 **Detailed insights** - Scores, strengths, concerns, and interview priorities  
🔄 **Gets smarter** - Learns from your feedback to match your preferences  
🚀 **Powered by GPT-5** - Latest AI models with automatic fallback

```
Drop Files → AI Analysis → Ranked Results → Your Feedback → Improved Rankings
```

## ✨ Key Features

- 🎯 **Structured evaluations** with scores (0-100) and recommendations
- 📈 **Interview priorities** (HIGH/MEDIUM/LOW) to focus your time
- 💡 **AI learning** from your feedback improves future screenings
- 📄 **Multiple formats** - CSV reports and HTML summaries
- 🔒 **Privacy-first** - All data stays local, only candidate content goes to OpenAI
- ⚡ **Fast** - Process multiple candidates in seconds

## 🚀 5-Minute Setup

**Prerequisites:** Python 3.9+, OpenAI API key ([get one here](https://platform.openai.com/api-keys))

```bash
# 1. Clone and install
git clone <repo-url>
cd ai_job_candidate_reviewer
pip3 install -r requirements.txt

# 2. Configure API key
echo "OPENAI_API_KEY=sk-proj-your-key-here" > .env

# 3. Verify it works
python3 candidate_reviewer.py test-connection
```

**That's it!** You're ready to start screening candidates.

---

## 📚 Table of Contents

- [Quick Start Guide](#quick-start-guide) - Get up and running fast
- [Environment Configuration](#environment-configuration) - API keys and data paths
- [File Organization](#file-organization) - How files are structured
- [All Commands](#all-commands) - Complete command reference
- [Results & Reports](#results) - Understanding the output
- [Advanced Features](#optional-improve-results) - Fine-tune AI behavior
- [Troubleshooting](#troubleshooting) - Common issues

---

## 🎬 Quick Start Guide

### Step 1: Setup a Job (once per position)

```bash
# Create the data directory
mkdir -p data/intake

# Drop these files into data/intake/:
# - job_description.pdf (required)
# - ideal_candidate.txt (optional - helps AI understand what you want)
# - warning_flags.txt (optional - red flags to watch for)

# Process the job
python3 candidate_reviewer.py setup-job "senior_engineer"
```

### Step 2: Process Candidates (ongoing)

```bash
# Drop candidate files into data/intake/:
# - resume_john_doe.pdf
# - coverletter_john_doe.pdf (optional)
# - application_john_doe.txt (optional)

# Process them
python3 candidate_reviewer.py process-candidates "senior_engineer"
```

### Step 3: Review Rankings

```bash
# See ranked candidates in terminal
python3 candidate_reviewer.py show-candidates "senior_engineer"

# Or open detailed HTML report in browser
python3 candidate_reviewer.py open-reports "senior_engineer"
```

### Step 4: Teach the AI (optional but powerful)

```bash
# Give feedback on evaluations
python3 candidate_reviewer.py provide-feedback "senior_engineer" "john_doe" \
  "Too much weight on years of experience, not enough on practical skills"

# Re-evaluate with improved AI
python3 candidate_reviewer.py re-evaluate "senior_engineer"
```

**💡 Pro Tip:** The AI learns from your feedback and applies those insights to future evaluations!

---

## ⚠️ Important Notes

- **AI assists, humans decide** - Always review AI evaluations before hiring decisions
- **Privacy** - Candidate data is sent to OpenAI for analysis per their privacy policy
- **Continuous improvement** - The system gets better with your feedback
- **Model visibility** - Every command shows which AI model is being used



---

## 🔧 Environment Configuration

### Required: OpenAI API Key

Create a `.env` file in the project root with your OpenAI API key:

```bash
OPENAI_API_KEY=sk-proj-your-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### Optional: Data Storage Path

By default, all data is stored in `./data/`. You can customize this with environment variables:

```bash
# Change base data directory (useful for testing or custom storage)
BASE_DATA_PATH=./custom_data

# Or override individual paths
INTAKE_PATH=./my_intake
JOBS_PATH=./my_jobs
CANDIDATES_PATH=./my_candidates
OUTPUT_PATH=./my_output
```

**Directory Structure:**

The application automatically creates these subdirectories if they don't exist:

```
{BASE_DATA_PATH}/          # Default: ./data
├── intake/                # Drop files here for processing
├── jobs/                  # Processed job descriptions (auto-created)
├── candidates/            # Processed candidate files (auto-created)
└── output/                # Generated reports (auto-created)
```

**You only need to create the base directory** (e.g., `mkdir data` or `mkdir custom_data`). The subdirectories are created automatically when you run commands.

**Common use cases:**
- **Testing:** `BASE_DATA_PATH=./test_data` (keeps test data separate)
- **Production:** `BASE_DATA_PATH=/var/app/data` (system-wide storage)
- **Development:** `BASE_DATA_PATH=./data_dev` (separate dev environment)

**Note:** These are optional. For normal use, just set `OPENAI_API_KEY` and use the default `./data/` directory.

For more configuration options, see `CONFIGURATION.md`.

---

## 📂 File Organization

**1. Drop files here:**

Example for `--setup-job` 
```
data/intake/
├── job_description.pdf              # Required for --setup-job
├── ideal_candidate.txt              # Optional for --setup-job  
├── warning_flags.txt                # Optional for --setup-job

```
Example for `process-candidates`
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

---

## 📖 All Commands

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

---

## 📊 Results & Reports

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

---

## 📝 File Naming

**Job files:** Any names work, script auto-detects
**Candidate files:** Include name in filename
- `resume_john_doe.pdf` → Candidate: "john_doe"
- `JohnDoe_CV.pdf` → Candidate: "johndoe"

---

## 🎯 Advanced: Improve Results

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

---

## 🔧 Troubleshooting

**Common Issues:**

| Problem | Solution |
|---------|----------|
| ❌ Missing API key | Add `OPENAI_API_KEY` to `.env` file ([get key](https://platform.openai.com/api-keys)) |
| ❌ No job description | Drop a job description PDF into `data/intake/` |
| ❌ No candidates found | Ensure resume filenames include candidate names (e.g., `resume_john_doe.pdf`) |
| ❌ File size errors | Check `MAX_FILE_SIZE_MB` setting (default: 2MB) |
| ❌ Wrong data directory | Verify `BASE_DATA_PATH` environment variable |

**Still stuck?** Check out:
- `GETTING_STARTED.md` - Detailed setup guide
- `CONFIGURATION.md` - All configuration options
- `DEVELOPMENT.md` - Development workflow and testing

---

## 🤝 Contributing

Found a bug? Have an idea? Contributions are welcome!

1. Check existing issues or create a new one
2. Fork the repository
3. Make your changes
4. Run `./pre-push.sh` to validate
5. Submit a pull request

See `DEVELOPMENT.md` for development setup and guidelines.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

This software is provided "as-is" for evaluation and screening assistance. The AI-generated evaluations should be reviewed by humans before making hiring decisions.

---

## 🙏 Acknowledgments

Built with:
- 🤖 OpenAI GPT-5 / GPT-4
- 🐍 Python 3.9+
- 📦 Click, Pydantic, pypdf

---

**Ready to transform your hiring process?** [Get started now](#🚀-5-minute-setup) 🚀
