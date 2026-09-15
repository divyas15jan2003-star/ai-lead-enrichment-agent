# AI Lead Enrichment Agent

A Python-based autonomous company intelligence and lead enrichment pipeline that crawls company websites, cleans web content, extracts structured company information using an LLM, discovers leadership LinkedIn profiles, calculates confidence scores, and tracks LLM token usage.

This project was developed as a practical AI Engineer Intern take-home assignment.

---

## 1. Project Overview

The AI Lead Enrichment Agent accepts a list of company domains and automatically performs the following workflow:

1. Crawls the company website.
2. Discovers relevant internal pages such as About, Team, Company, Contact, Customers, Solutions, Pricing, and Careers.
3. Uses a headless Chromium browser to handle JavaScript-rendered websites.
4. Cleans the retrieved HTML before sending content to the LLM.
5. Builds a token-efficient context from the relevant pages.
6. Uses an LLM with structured JSON output to extract company intelligence.
7. Extracts public/generic email addresses.
8. Identifies leadership and team members when supported by the website content.
9. Discovers LinkedIn profile URLs from the website.
10. Uses external search to enrich missing LinkedIn profiles when possible.
11. Calculates a confidence score for each company profile.
12. Tracks LLM token usage.
13. Continues processing even when an individual website fails.

The pipeline was tested using:

- `postman.com`
- `supabase.com`
- `vapi.ai`

---

## 2. Key Features

### Website Crawling

- Headless browser-based crawling using Playwright.
- Handles JavaScript-rendered websites.
- Starts from the company homepage.
- Discovers relevant internal pages automatically.
- Prioritizes pages related to:
  - About
  - Team
  - Leadership
  - Founders
  - Company
  - Contact
  - Customers
  - Solutions
  - Pricing
  - Careers
  - Press

### Content Cleaning

Raw HTML is not directly sent to the LLM.

The content cleaning layer:

- Removes JavaScript.
- Removes CSS.
- Removes SVG elements.
- Removes iframes and other unnecessary elements.
- Removes navigation, header, and footer boilerplate.
- Extracts meaningful headings, paragraphs, lists, and blockquotes.
- Removes duplicate content.
- Normalizes whitespace.
- Removes common website noise.
- Limits the amount of content passed to the LLM.

This reduces unnecessary tokens and improves extraction quality.

### Structured LLM Extraction

The LLM extracts:

- Company overview
- Target audience / ideal customer profile
- Public email addresses
- Leadership/team members
- Roles
- LinkedIn URLs when available
- Source URLs

The extraction uses Pydantic schemas and structured JSON output.

The system is instructed not to invent information when it is not supported by the supplied website content.

### LinkedIn Discovery

The system supports two levels of LinkedIn discovery.

#### 1. Website-based discovery

LinkedIn URLs present on crawled company pages are extracted automatically.

#### 2. External search enrichment

When a leadership member does not have a LinkedIn URL, the pipeline can use Tavily search to look for a matching public LinkedIn profile.

Additional validation is performed using:

- Person name matching
- LinkedIn profile URL validation
- Search result content
- Company/domain matching

This helps reduce false-positive LinkedIn matches.

### Error Handling

The pipeline is designed to continue processing when individual websites fail.

It handles cases such as:

- Invalid domains
- DNS failures
- Page timeouts
- HTTP errors
- 404 pages
- 5xx server errors
- Missing content
- Missing leadership information
- Missing LinkedIn profiles
- External search failures

A failed company does not stop the complete pipeline.

### Confidence Scoring

Each extracted company profile receives a confidence score between:

```text
0.0 - 1.0
```

The score considers the availability of:

- Company overview
- Target audience
- Contact information
- Leadership information
- LinkedIn information
- Source URLs
- Number of successfully crawled pages

### Token Usage Tracking

The system tracks LLM usage for the complete run.

Tracked metrics include:

- Number of LLM calls
- Input tokens
- Output tokens
- Total tokens
- Estimated cost

Example:

```json
{
  "llm_calls": 3,
  "input_tokens": 13290,
  "output_tokens": 2254,
  "total_tokens": 15544,
  "estimated_cost_usd": 0.0
}
```

The estimated cost remains `0.0` unless model-specific pricing is configured.

---

## 3. Architecture

The overall pipeline follows this architecture:

```text
                    ┌──────────────────┐
                    │   domains.json   │
                    └────────┬─────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Website Crawler   │
                  │     Playwright      │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │  Relevant Webpages  │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │  Content Cleaner    │
                  │ BeautifulSoup +     │
                  │ text extraction     │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │  Context Builder    │
                  │ Token-efficient     │
                  │ context             │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │   LLM Extraction    │
                  │       Groq          │
                  │ Structured JSON      │
                  └─────────┬───────────┘
                            │
                ┌───────────┴────────────┐
                ▼                        ▼
      ┌──────────────────┐      ┌──────────────────┐
      │ LinkedIn Matcher │      │ LinkedIn Search  │
      │ Website URLs     │      │ Tavily Search    │
      └────────┬─────────┘      └────────┬─────────┘
               │                         │
               └────────────┬────────────┘
                            ▼
                  ┌─────────────────────┐
                  │ Confidence Scoring  │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │     output.json     │
                  └─────────────────────┘

                            +
                  ┌─────────────────────┐
                  │   Usage Tracker     │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │     usage.json      │
                  └─────────────────────┘
```

---

## 4. Project Structure

```text
ai-lead-enrichment-agent/
│
├── src/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── crawler.py
│   ├── content_cleaner.py
│   ├── context_builder.py
│   ├── extractor.py
│   ├── confidence.py
│   ├── linkedin_matcher.py
│   ├── linkedin_search.py
│   ├── usage_tracker.py
│ 
│
├── output/
│   ├── output.json
│   └── usage.json
│
├── domains.json
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Main pipeline orchestration |
| `config.py` | Environment variables and configuration |
| `schemas.py` | Pydantic data models |
| `crawler.py` | Website crawling and page discovery |
| `content_cleaner.py` | HTML cleaning and text extraction |
| `context_builder.py` | Builds token-efficient LLM context |
| `extractor.py` | LLM-based structured extraction |
| `confidence.py` | Confidence score calculation |
| `linkedin_matcher.py` | Matches website LinkedIn URLs to people |
| `linkedin_search.py` | External LinkedIn profile discovery |
| `usage_tracker.py` | Tracks LLM token usage and estimated cost |
| `utils.py` | Utility/helper functions |

---

## 5. Technologies Used

### Programming Language

- Python 3.10+

### Web Crawling

- Playwright
- Chromium

### HTML Processing

- BeautifulSoup4

### Data Validation

- Pydantic

### LLM

- Groq API
- `openai/gpt-oss-20b`

### External Search

- Tavily

### Configuration

- python-dotenv

---

## 6. Requirements

Before running the project, make sure the following are installed:

- Python 3.10 or later
- pip
- Internet connection
- Groq API key
- Tavily API key

---

## 7. Installation

### Step 1: Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Move into the project directory:

```bash
cd ai-lead-enrichment-agent
```

---

### Step 2: Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4: Install Playwright Chromium

```bash
playwright install chromium
```

---

## 8. Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
TAVILY_API_KEY=your_tavily_api_key
```

### Environment Variable Description

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | API key used for LLM extraction |
| `GROQ_MODEL` | Groq model used by the extractor |
| `TAVILY_API_KEY` | API key used for external LinkedIn search |

### Security

API keys must never be committed to GitHub.

The `.env` file should remain local.

Use `.env.example` as a template.

---

## 9. Input

The input file is:

```text
domains.json
```

Example:

```json
[
  "postman.com",
  "supabase.com",
  "vapi.ai"
]
```

You can replace these domains with other publicly accessible company domains.

---

## 10. Running the Pipeline

Make sure the virtual environment is activated.

Then run:

```bash
python -m src.main
```

The pipeline will process each domain sequentially.

Example terminal output:

```text
======================================================================
PROCESSING: postman.com
======================================================================
✓ Crawled pages: 6
✓ Context size: 24042 characters
✓ LinkedIn URLs discovered: 4
✓ LLM extraction completed
✓ Confidence score: 1.0

======================================================================
PROCESSING: supabase.com
======================================================================
✓ Crawled pages: 6
✓ Context size: 20550 characters
✓ LinkedIn URLs discovered: 0
✓ LLM extraction completed
✓ Confidence score: 0.6

======================================================================
PROCESSING: vapi.ai
======================================================================
✓ Crawled pages: 4
✓ Context size: 6706 characters
✓ LinkedIn URLs discovered: 1
✓ LLM extraction completed
✓ Confidence score: 0.7
```

At the end, the pipeline writes:

```text
output/output.json
output/usage.json
```

---

## 11. Output

### Company Output

The main result is stored in:

```text
output/output.json
```

Example structure:

```json
[
  {
    "company_overview": "Company overview...",
    "target_audience": "Target audience...",
    "contact_points": [
      "info@example.com"
    ],
    "leadership": [
      {
        "name": "Example Person",
        "role": "CEO",
        "linkedin_url": "https://www.linkedin.com/in/example",
        "source": "https://example.com/about"
      }
    ],
    "sources": [
      "https://example.com/about"
    ],
    "domain": "example.com",
    "confidence_score": 0.9
  }
]
```

---

### Usage Output

LLM usage information is stored in:

```text
output/usage.json
```

Example:

```json
{
  "llm_calls": 3,
  "input_tokens": 13290,
  "output_tokens": 2254,
  "total_tokens": 15544,
  "estimated_cost_usd": 0.0
}
```

---

## 12. Structured Data Schema

The extraction pipeline uses Pydantic models to validate the LLM response.

### Leadership Member

```text
name
role
linkedin_url
source
```

### Company Profile

```text
domain
company_overview
target_audience
contact_points
leadership
confidence_score
sources
```

The schema prevents malformed data from entering the final output.

---

## 13. LLM Extraction Strategy

The LLM receives cleaned website content instead of raw HTML.

The extraction prompt explicitly instructs the model to:

- Use only supplied website content.
- Avoid guessing.
- Avoid fabricating information.
- Return empty values when information is unavailable.
- Extract only public email addresses.
- Extract leadership only when supported by evidence.
- Avoid fabricating LinkedIn URLs.
- Include source URLs supporting extracted information.

Structured JSON output is used to make the extraction predictable and machine-readable.

---

## 14. Web Crawling Strategy

The crawler begins with the company homepage and discovers internal links.

Pages are ranked using relevance keywords.

Higher priority is given to URLs containing terms such as:

```text
leadership
team
founders
about
company
contact
customers
solutions
pricing
careers
press
```

The crawler has a maximum page limit to prevent unnecessary crawling.

The current pipeline uses:

```text
Maximum pages: 6
Page timeout: 30 seconds
Retries: 2
```

---

## 15. Content Cleaning Strategy

The cleaner removes unnecessary website content before LLM processing.

Removed elements include:

```text
script
style
svg
noscript
iframe
canvas
template
video
audio
nav
footer
header
```

The cleaner prioritizes:

```text
h1
h2
h3
h4
p
li
blockquote
```

This helps reduce:

- Token usage
- LLM latency
- Irrelevant context
- Prompt size

---

## 16. Error Resilience

A major design goal is that one failed website should not terminate the entire pipeline.

For example:

```text
Company A → Success
Company B → Timeout
Company C → Success
```

The pipeline still produces results for Company A and Company C.

The crawler retries temporary failures and gracefully handles unsuccessful requests.

The main pipeline also catches company-level exceptions and records an error instead of crashing the entire run.

---

## 17. LinkedIn Enrichment

LinkedIn enrichment follows this process:

```text
Crawled Website
       │
       ▼
Extract LinkedIn URLs
       │
       ▼
Match URLs with leadership names
       │
       ├── Match found → Use profile
       │
       └── No match
             │
             ▼
        Tavily Search
             │
             ▼
       Validate result
             │
             ├── Valid → Add LinkedIn URL
             │
             └── Invalid → Leave empty
```

The external search layer intentionally rejects uncertain matches rather than returning potentially incorrect profiles.

---

## 18. Confidence Scoring

The confidence score is calculated using available evidence.

The score considers:

- Whether an overview was extracted
- Whether a target audience was identified
- Whether contact information was found
- Whether leadership information was found
- Whether LinkedIn information was found
- Whether source URLs were available
- Number of successfully crawled pages

The final value is constrained to:

```text
0.0 <= confidence_score <= 1.0
```

---

## 19. Token and Cost Tracking

The `UsageTracker` records usage from every LLM request.

For each call, it records:

```text
Input tokens
Output tokens
Total tokens
```

The tracker aggregates usage across all companies.

Example:

```text
LLM calls:       3
Input tokens:    13290
Output tokens:   2254
Total tokens:    15544
```

Estimated cost is calculated using configurable input/output price values.

The default price values are `0.0` so that the project does not assume or hard-code unverified pricing.

---

## 20. Sample Test Domains

The pipeline was tested with:

```text
postman.com
supabase.com
vapi.ai
```

The system successfully demonstrated:

- Multi-page crawling
- Dynamic website handling
- Content cleaning
- Structured LLM extraction
- Leadership extraction
- Website-based LinkedIn discovery
- External LinkedIn enrichment
- Confidence scoring
- Token tracking
- Graceful failure handling

---

## 21. Design Decisions

### Why Playwright?

Playwright provides a real browser environment and can process JavaScript-rendered websites that may not expose all content through simple HTTP requests.

### Why BeautifulSoup?

BeautifulSoup provides lightweight HTML parsing and makes it easier to remove unwanted elements and extract meaningful text.

### Why Pydantic?

Pydantic provides runtime validation for structured LLM responses and ensures the final data follows a predictable schema.

### Why Groq?

Groq provides access to LLMs through an API with fast inference and was used for the implementation of the extraction layer.

### Why Tavily?

Tavily provides external web search capability that can be used to discover LinkedIn profiles when the company website does not expose them directly.

---

## 22. Limitations

The current implementation has several practical limitations:

1. Some websites may block automated browsers.
2. Websites with strong bot protection may not be crawlable.
3. Some leadership information may not be publicly available.
4. LinkedIn search results can change over time.
5. External LinkedIn discovery depends on search result quality.
6. Some websites may use complex navigation that cannot be discovered automatically.
7. Confidence scores are heuristic rather than statistically calibrated.
8. Estimated cost depends on configured model pricing.

---

## 23. Future Improvements

Potential future improvements include:

- More advanced agentic browser navigation.
- LangGraph or Browser-Use based agent workflows.
- Search-engine fallback strategies.
- Better company-name detection.
- More sophisticated entity matching.
- Improved confidence calibration.
- Parallel company processing.
- Persistent caching.
- Database storage.
- Retry queues.
- Observability and structured logging.
- Per-company token/cost breakdown.
- CSV export.
- Additional LLM provider support.
- Automated evaluation against labeled datasets.

---

## 24. Example Workflow

Given:

```json
[
  "example.com"
]
```

The agent performs:

```text
Input Domain
     ↓
Homepage Fetch
     ↓
Internal Link Discovery
     ↓
Relevant Page Selection
     ↓
Headless Browser Crawling
     ↓
HTML Cleaning
     ↓
Context Construction
     ↓
LLM Structured Extraction
     ↓
Email Validation
     ↓
Leadership Extraction
     ↓
LinkedIn Matching
     ↓
External LinkedIn Search
     ↓
Confidence Calculation
     ↓
JSON Output
     ↓
Token Usage Report
```

---

## 25. GitHub Security

Before pushing the project to GitHub, verify that the following files are NOT committed:

```text
.env
venv/
__pycache__/
```

API keys must never be included in source code or documentation.

The repository should contain:

```text
.env.example
```

instead of the real `.env` file.

---

## 26. Quick Start

For a quick setup:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ai-lead-enrichment-agent

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

playwright install chromium
```

Create `.env`:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
TAVILY_API_KEY=your_tavily_api_key
```

Then run:

```bash
python -m src.main
```

Results will be available in:

```text
output/output.json
output/usage.json
```

---

## 27. Assignment Operations Requirement

The project is designed with the operational requirements of the AI Engineer Intern role in mind.

I am comfortable with a role involving approximately 40% manual operational work such as lead prospecting, email verification, LinkedIn account handling, prospect discovery, lead verification, and dataset cleaning, alongside approximately 60% AI agent engineering and automation work.

---

## 28. Author

**Name:** Divya S

**Role:** AI Engineer Intern Candidate

**LinkedIn:** www.linkedin.com/in/divya-s-178a09303


**GitHub:** https://github.com/divyas15jan2003-star

---

## 29. License

This project was created as a technical take-home assignment for evaluation purposes.