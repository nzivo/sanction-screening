from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/sanctions_db"
    ofac_api_key: str = ""
    update_interval_hours: int = 24
    fuzzy_match_threshold: int = 80
    
    # Sanctions list URLs
    ofac_sdn_url: str = "https://www.treasury.gov/ofac/downloads/sdn.xml"
    ofac_consolidated_url: str = "https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml"
    un_consolidated_url: str = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    eu_sanctions_url: str = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token="
    uk_sanctions_url: str = "https://www.gov.uk/government/publications/financial-sanctions-consolidated-list-of-targets/consolidated-list-of-targets"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
