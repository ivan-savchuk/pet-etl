
CREATE SCHEMA youtube;

CREATE TABLE youtube.videos (
    "video_id" VARCHAR PRIMARY KEY,
    "title" VARCHAR,
    "views" BIGINT,
    "country_code" VARCHAR,
    "extract_date" DATE,
    "allowed_regions" JSON,
    "blocked_regions" JSON,
    "caption" TEXT,
    "category_id" VARCHAR,
    "channel_id" VARCHAR,
    "channel_name" VARCHAR,
    "comment" BIGINT,
    "definition" VARCHAR,
    "description" VARCHAR,
    "image_dimension" VARCHAR,
    "dislikes" BIGINT,
    "video_duration" VARCHAR,
    "favorite" VARCHAR,
    "license_status" BOOLEAN,
    "likes" BIGINT,
    "live_status" VARCHAR,
    "local_description" VARCHAR,
    "local_title" VARCHAR,
    "publish_time" TIMESTAMP,
    "tags" JSON,
    "thumbnail_height" INTEGER,
    "thumbnail_url" VARCHAR,
    "thumbnail_width" INTEGER
);
