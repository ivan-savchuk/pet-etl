import logging
import json
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from utils.config import Config
from parsers.youtube import YouTube
from utils.compose_names import compose_s3_key
from repo.s3.bucket import Bucket


CONFIG = Config.get_config()
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(module)s(%(lineno)d) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)


def lambda_handler(event: dict, context: dict) -> dict:
    logging.info("Provided event: '%s', and context '%s'.", event, context)
    youtube = YouTube(
        url=CONFIG["url"],
        api_key=CONFIG["api_key"],
        country_codes=CONFIG["country_codes"]
    )
    trends = youtube.get_trends()
    s3_keys = [compose_s3_key(trend) for trend in trends]
    bucket = Bucket()
    with ThreadPoolExecutor(max_workers=len(CONFIG["country_codes"])) as executor:
        futures = [
            executor.submit(bucket.put_object, CONFIG["bucket"], key, trend.to_json()) 
            for key, trend in zip(s3_keys, trends)
        ]
        for f in futures:
            if f.exception() is not None:
                raise f.exception()
    return {
        "statusCode": 200,
        "body": json.dumps("Trends were succussfully extracted and saved!")
    }
