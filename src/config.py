import os

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------
# Groq configuration
# ---------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)


# Current Groq pricing for openai/gpt-oss-20b
# Prices are USD per 1 million tokens.
GROQ_INPUT_COST_PER_MILLION = 0.075
GROQ_OUTPUT_COST_PER_MILLION = 0.30


# ---------------------------------------------------------
# Tavily configuration
# ---------------------------------------------------------

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not configured. "
        "Please add it to your .env file."
    )