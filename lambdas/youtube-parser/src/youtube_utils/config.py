import os


class Config:
    """Class to store configuration variables"""
    _cfg: dict[str, str] = {}

    @classmethod
    def get_config(cls) -> dict[str, str | list]:
        if not cls._cfg:
            cls._cfg = {
                "bucket": os.environ.get("BUCKET_NAME", ""),
                "url": os.environ.get("YOUTUBE_URL", ""),
                "country_codes": os.environ.get("COUNTRY_CODES", "").split(","),
            }
            cls.__validate_config(cls._cfg)
        return cls._cfg

    @staticmethod
    def __validate_config(cfg: dict[str, str]) -> None:
        for key, value in cfg.items():
            if key == "country_codes":
                if not value or len(value) == 0:
                    raise ValueError("Country codes are not set")
                continue
            if not value or len(value) == 0:
                raise ValueError(f"Config variable {key} is not set")
