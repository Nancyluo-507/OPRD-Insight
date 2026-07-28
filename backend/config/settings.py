import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=os.path.abspath(_env_path))


class Settings:
    @staticmethod
    def get(key: str, default=None):
        return os.getenv(key, default)

    # Server
    CORS_ORIGINS: str = get("CORS_ORIGINS", "*")
    PUBLIC_URL: str = get("PUBLIC_URL", "http://localhost:8000")

    # Auth
    JWT_SECRET: str = get("JWT_SECRET", "")
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not set. Add JWT_SECRET=your-random-secret to .env")
    JWT_EXPIRY_DAYS: int = int(get("JWT_EXPIRY_DAYS", "7"))

    # Database
    DATA_DIR: str = get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
    DATABASE_URL: str = get("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'papers.db')}")

    # Email (SendGrid)
    SENDGRID_API_KEY: str = get("SENDGRID_API_KEY", "")

    # Email (SMTP)
    SMTP_HOST: str = get("SMTP_HOST", "")
    SMTP_PORT: int = int(get("SMTP_PORT", "465"))
    SMTP_USER: str = get("SMTP_USER", "")
    SMTP_PASS: str = get("SMTP_PASS", "")
    SMTP_FROM: str = get("SMTP_FROM", get("EMAIL_FROM", "ChemVigil <noreply@chemvigil.app>"))

    # Email (Resend)
    RESEND_API_KEY: str = get("RESEND_API_KEY", "")

    # Translation (Baidu)
    BAIDU_APP_ID: str = get("BAIDU_APP_ID", "")
    BAIDU_API_KEY: str = get("BAIDU_API_KEY", "")
    BAIDU_SECRET_KEY: str = get("BAIDU_SECRET_KEY", "")

    # CrossRef
    CROSSREF_EMAIL: str = get("CROSSREF_EMAIL", "nancy@boehringer-ingelheim.com")
    CROSSREF_API_KEY: str = get("CROSSREF_API_KEY", "")

    # OpenAlex
    OPENALEX_API_KEY: str = get("OPENALEX_API_KEY", "")

    # OpenAlex
    OPENALEX_URL: str = get("OPENALEX_URL", "https://api.openalex.org/works")
    OPENALEX_TIMEOUT: int = int(get("OPENALEX_TIMEOUT", "30"))
    OPENALEX_USER_AGENT: str = get("OPENALEX_USER_AGENT", "OPRD-Insight/1.0")
    OPENALEX_PER_PAGE: int = int(get("OPENALEX_PER_PAGE", "50"))

    # PubMed
    PUBMED_EMAIL: str = get("PUBMED_EMAIL", "nancy@boehringer-ingelheim.com")

    # Source Priority (higher = better)
    SOURCE_PRIORITY: dict = {
        "OpenAlex": 100,
        "PubMed": 80,
        "CrossRef": 50,
        "LocalDB": 10,
    }


settings = Settings()
