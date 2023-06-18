import sys
from datetime import datetime

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col
from pyspark.sql.types import StringType


def transform_to_time(value: str) -> str:
    stripped_time = value.strip("PT")
    time_with_colons = stripped_time.replace("H", ":").replace("M", ":").replace("S", "")
    split_time = time_with_colons.split(":")
    if len(split_time) == 3:
        if len(split_time[0]) == 1:
            split_time[0] = f"0{split_time[0]}"
        if len(split_time[1]) == 1:
            split_time[1] = f"0{split_time[1]}"
        if len(split_time[2]) == 1:
            split_time[2] = f"0{split_time[2]}"
        return f"{split_time[0]}:{split_time[1]}:{split_time[2]}"
    if len(split_time) == 2:
        if len(split_time[0]) == 1:
            split_time[0] = f"0{split_time[0]}"
        if len(split_time[1]) == 1:
            split_time[1] = f"0{split_time[1]}"
        return f"00:{split_time[0]}:{split_time[1]}"
    if len(split_time) == 1:
        if len(split_time[0]) == 1:
            split_time[0] = f"0{split_time[0]}"
        return f"00:00:{split_time[0]}"

    return "00:00:00"


args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "PG_PASSWORD",
        "PG_HOST",
        "PG_PORT",
        "PG_DATABASE",
        "PG_USER",
        "DESTINATION_TABLE"
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

time_udf = spark_glue.udf.register("duration", transform_to_time, StringType())
flattened_df = flattened_df.withColumn("duration", time_udf(col("duration")))
flattened_df = flattened_df.withColumnRenamed("duration", "video_duration")

logger.info("Writing data to Postgres")
flattened_df.write.jdbc(
    url=f"jdbc:postgresql://{args['PG_HOST']}:{args['PG_PORT']}/{args['PG_DATABASE']}",
    table=args["DESTINATION_TABLE"],
    mode="append",
    properties={
        "user": args["PG_USER"],
        "password": args["PG_PASSWORD"],
        "driver": "org.postgresql.Driver"
    }
)

logger.info("Job finished, committing...")
job.commit()
