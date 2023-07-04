import sys

import boto3
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, avg, coalesce, round, count, lit  # pylint: disable=redefined-builtin


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

spark_session = SparkSession.builder.appName("agg_json").getOrCreate()
sc = spark_session.sparkContext
glue_context = GlueContext(sc)
spark_glue = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)

logger = glue_context.get_logger()
logger.info(f"Starting Job {args['JOB_NAME']}")

logger.info("Reading data from Postgres")
pg_creds = get_ssm_parameter("pg_db_creds").split(",")
df = spark_glue.read \
    .format("jdbc") \
    .option("url", f"jdbc:postgresql://{pg_creds[-2]}:{pg_creds[0]}/{pg_creds[-1]}") \
    .option("dbtable", get_ssm_parameter("glue_destination_table")) \
    .option("user", pg_creds[1]) \
    .option("password", pg_creds[2]) \
    .option("driver", "org.postgresql.Driver") \
    .load()

youtubers_trends_stats = df.groupby("channel_name") \
    .agg(
    round(coalesce(sum("views"), lit(0)), 2).alias("total_views"),
    round(coalesce(avg("views"), lit(0)), 2).alias("views_on_average"),
    round(coalesce(sum("likes"), lit(0)), 2).alias("total_likes"),
    round(coalesce(avg("likes"), lit(0)), 2).alias("likes_on_average"),
    count("channel_name").alias("total_videos_in_trends")
) \
    .orderBy(
    "total_views", "views_on_average",
    "total_likes", "likes_on_average",
    "total_videos_in_trends"
)
countries_stats = df.groupby("country_code") \
    .agg(
    round(coalesce(sum("views"), lit(0)), 2).alias("total_views"),
    round(coalesce(avg("views"), lit(0)), 2).alias("views_on_average"),
    round(coalesce(sum("likes"), lit(0)), 2).alias("total_likes"),
    round(coalesce(avg("likes"), lit(0)), 2).alias("likes_on_average")
) \
    .orderBy(
    "total_views", "views_on_average",
    "total_likes", "likes_on_average"
)

youtubers_trends_stats.write \
    .mode("overwrite") \
    .jdbc(
        table="youtubers_trends_stats",
        mode="overwrite",
        url=f"jdbc:postgresql://{pg_creds[-2]}:{pg_creds[0]}/{pg_creds[-1]}",
        properties={
            "driver": "org.postgresql.Driver",
            "user": pg_creds[1],
            "password": pg_creds[2]
        }
    )
countries_stats.write \
    .mode("overwrite") \
    .jdbc(
        table="countries_stats",
        mode="overwrite",
        url=f"jdbc:postgresql://{pg_creds[-2]}:{pg_creds[0]}/{pg_creds[-1]}",
        properties={
            "driver": "org.postgresql.Driver",
            "user": pg_creds[1],
            "password": pg_creds[2]
        }
    )

logger.info("Job finished, committing...")
job.commit()
