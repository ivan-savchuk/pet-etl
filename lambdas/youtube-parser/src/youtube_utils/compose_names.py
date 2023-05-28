from parsers.youtube import CountryTrends


def compose_s3_key(country_trends: CountryTrends) -> str:
    """Compose s3 key for country trends"""
    return f"{country_trends.extraction_date}/{country_trends.country_code}.json"
