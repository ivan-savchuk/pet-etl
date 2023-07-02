import sys
from datetime import datetime

import boto3
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col, when, regexp_replace, split, size, concat, lit, lpad


def transform_to_time(column):
    stripped_time = regexp_replace(column, "PT", "")
    time_with_colons = regexp_replace(stripped_time, "([HMS])", ":")
    split_time = split(time_with_colons, ":")
    split_time_len = size(split_time)

    hours_expr = when(split_time_len >= 3, split_time[0]).otherwise(lit("0"))
    minutes_expr = when(split_time_len >= 3, split_time[1]).when(split_time_len == 2, split_time[0])\
        .otherwise(lit("0"))
    seconds_expr = when(split_time_len >= 3, split_time[2]).when(split_time_len == 2, split_time[1])\
        .otherwise(split_time[0])

    hours_expr = lpad(hours_expr, 2, "0")
    minutes_expr = lpad(minutes_expr, 2, "0")
    seconds_expr = lpad(seconds_expr, 2, "0")

    duration_expr = when(seconds_expr != "00", concat(hours_expr, lit(":"), minutes_expr, lit(":"), seconds_expr))\
        .otherwise(concat(hours_expr, lit(":"), minutes_expr))

    return duration_expr


def get_ssm_parameter(parameter_name: str) -> str:
    ssm_client = boto3.client("ssm")
    return ssm_client.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )["Parameter"]["Value"]


args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME"
    ]
)

spark_session = SparkSession.builder.appName("transform_json").getOrCreate()
sc = spark_session.sparkContext
glue_context = GlueContext(sc)
spark_glue = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)

logger = glue_context.get_logger()
logger.info(f"Starting Job {args['JOB_NAME']}")

logger.info("Reading data from S3")
trends_df = glue_context.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths":
            [
                f"s3://pet-etl-raw-data-storage/{str(datetime.now().date())}/"
            ],
        "recurse": True
    },
    format="json"
).toDF()

logger.info("Transforming data")
exploded_df = trends_df.withColumn("videos", explode(col("videos")))
flattened_df = exploded_df.select(
    col("country_code"),
    col("extract_date").cast("date"),
    col("videos.allowed_region").alias("allowed_regions"),
    col("videos.blocked_region").alias("blocked_regions"),
    col("videos.caption").alias("caption"),
    col("videos.category_id").alias("category_id"),
    col("videos.channel_id").alias("channel_id"),
    col("videos.channel_name").alias("channel_name"),
    col("videos.comment").alias("comment").cast("bigint"),
    col("videos.definition").alias("definition"),
    col("videos.description").alias("description"),
    col("videos.dimension").alias("image_dimension"),
    col("videos.duration").alias("duration"),
    col("videos.license_status").alias("license_status").cast("boolean"),
    col("videos.like").alias("likes").cast("bigint"),
    col("videos.local_description").alias("local_description"),
    col("videos.local_title").alias("local_title"),
    col("videos.publish_time").alias("publish_time").cast("timestamp"),
    col("videos.tags").alias("tags"),
    col("videos.thumbnail_height").alias("thumbnail_height").cast("int"),
    col("videos.thumbnail_url").alias("thumbnail_url"),
    col("videos.thumbnail_width").alias("thumbnail_width").cast("int"),
    col("videos.title").alias("title"),
    col("videos.video_id").alias("video_id"),
    col("videos.view").alias("views").cast("bigint")
)

flattened_df = flattened_df.withColumn("duration", transform_to_time(col("duration")))
flattened_df = flattened_df.withColumnRenamed("duration", "video_duration")

logger.info("Writing data to Postgres")
pg_creds = get_ssm_parameter("pg_db_creds").split(",")
flattened_df.write.jdbc(
    url=f"jdbc:postgresql://{pg_creds[-2]}:{pg_creds[0]}/{pg_creds[-1]}",
    table=get_ssm_parameter("glue_destination_table"),
    mode="append",
    properties={
        "user": pg_creds[1],
        "password": pg_creds[2],
        "driver": "org.postgresql.Driver"
    }
)

logger.info("Job finished, committing...")
job.commit()
