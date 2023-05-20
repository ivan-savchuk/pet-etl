import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dataclasses import dataclass

import requests
from requests.exceptions import RequestException


@dataclass
class Video:
    """Class to store video data"""
    _id: str
    snippet: dict[str, str]
    content_detail: dict[str, str]
    statistics: dict[str, int]

    def to_dict(self):
        """Convert video instance to dictionary."""
        snippet = {
            "publish_time": self.snippet.get("publishedAt"),
            "channel_id": self.snippet.get("channelId"),
            "title": self.snippet.get("title"),
            "description": self.snippet.get("description"),
            "thumbnail_url": self.snippet.get(
                "thumbnails", {}).get("high").get("url"),
            "thumbnail_width": self.snippet.get(
                "thumbnails", {}).get("high").get("width"),
            "thumbnail_height": self.snippet.get(
                "thumbnails", {}).get("high").get("height"),
            "channel_name": self.snippet.get("channelTitle"),
            "tags": self.snippet.get("tags"),
            "category_id": self.snippet.get("categoryId"),
            "live_status": self.snippet.get(
                "liveBroadcastContent"),
            "local_title": self.snippet.get(
                "localized", {}).get("title"),
            "local_description": self.snippet.get(
                "localized", {}).get("description"),
        }
        content = {
            "duration": self.content_detail.get("duration"),
            "dimension": self.content_detail.get("dimension"),
            "definition": self.content_detail.get(
                "definition"),
            "caption": self.content_detail.get("caption"),
            "license_status": self.content_detail.get(
                "licensedContent"),
            "allowed_region": self.content_detail.get(
                "regionRestriction", {}).get("allowed"),
            "blocked_region": self.content_detail.get(
                "regionRestriction", {}).get("blocked"),
        }
        statistics = {
            "view": self.statistics.get("viewCount"),
            "like": self.statistics.get("likeCount"),
            "dislike": self.statistics.get("dislikeCount"),
            "favorite": self.statistics.get("favoriteCount"),
            "comment": self.statistics.get("commentCount")
        }
        video_id = {"video_id": self._id}

        return {**video_id, **snippet, **content, **statistics}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class CountryTrends:
    """Class to parse country YouTube trends"""
    country_code: str
    extraction_date: str
    videos: list[Video]

    def to_dict(self) -> dict:
        trends_dict = {
            "country_code": self.country_code,
            "extract_date": self.extraction_date,
            "videos": [video.to_dict() for video in self.videos]
        }
        return trends_dict

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class YouTube:
    """Class to parse YouTube trending page"""
    def __init__(self, url: str, api_key: str, country_codes: list[str]) -> None:
        self._url = url
        self._api_key = api_key
        self.country_codes = country_codes

    def _get(self, payload: dict[str, int | str]) -> dict:
        try:
            res = requests.get(self._url, timeout=10, params=payload)
            res.raise_for_status()
        except RequestException as err:
            logging.error("Could not get YouTube trends: %s", err)
            logging.error("Could not extract data for region: %s", payload["regionCode"])
            return {}
        return res.json()

    def _get_country_trends(self, country_code: str) -> CountryTrends:
        logging.info("Getting YouTube trends for country: %s", country_code)
        payload = {
            "key": self._api_key,
            "chart": "mostPopular",
            "part": "snippet,contentDetails,statistics",
            "regionCode": country_code,
            "maxResults": 50,
        }
        response = self._get(payload)
        if not response:
            return CountryTrends(
                country_code=country_code,
                extraction_date=str(datetime.now()),
                videos=[]
            )

        items = response.get("items")
        cursor = response.get("nextPageToken")
        while cursor:
            payload["pageToken"] = cursor
            response = self._get(payload)
            cursor = response.get("nextPageToken")
            items.extend(response.get("items"))

        videos = [
            Video(
                _id=video.get("id"),
                snippet=video.get("snippet"),
                content_detail=video.get("contentDetails"),
                statistics=video.get("statistics")
            )
            for video in items
        ]

        return CountryTrends(
            country_code=country_code,
            extraction_date=str(datetime.now()),
            videos=videos
        )

    def get_trends(self) -> list[CountryTrends]:
        with ThreadPoolExecutor(max_workers=50) as executor:
            trends = executor.map(self._get_country_trends, self.country_codes)
            return list(trends)
