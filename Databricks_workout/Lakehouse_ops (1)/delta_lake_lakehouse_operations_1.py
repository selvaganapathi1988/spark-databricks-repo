# Databricks notebook source
# MAGIC %md
# MAGIC ###DataLake (Deltalake) + Lakehouse (Deltatables) - using Delta format (parquet+snappy+delta log)

# COMMAND ----------

# MAGIC %md
# MAGIC Delta Lake is an open-source storage framework that brings reliability, ACID transactions, and performance to data lakes. It sits on top of Parquet files and is most commonly used with Apache Spark and Databricks.<br>
# MAGIC Delta Lake is the core storage layer behind Bronze–Silver–Gold (medallion) architectures.
# MAGIC <img src="https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-logo-whitebackground.png" style="width:300px; float: right"/>
# MAGIC
# MAGIC ## ![](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Creating our first Delta Lake table
# MAGIC
# MAGIC Delta is the default file and table format using Databricks.

# COMMAND ----------

# MAGIC %md
# MAGIC ![](https://docs.databricks.com/aws/en/assets/images/well-architected-lakehouse-7d7b521addc268ac8b3d597bafa8cae9.png)

# COMMAND ----------

#%sql
#drop table lakehousecat.deltadb.customer_txn;
#drop table lakehousecat.deltadb.customer_txn_part;
#drop table lakehousecat.deltadb.drugtargettable1;
#drop table lakehousecat.deltadb.drugtargettable1_merge;
#drop table lakehousecat.deltadb.drugtargettable1_partitioned;
#drop table lakehousecat.deltadb.employee_dv_demo1;
#drop table lakehousecat.deltadb.product_inventory;
#drop table lakehousecat.deltadb.tblsales;

# COMMAND ----------

#spark.sql(f"drop catalog if exists lakehousecat1 cascade")
spark.sql(f"CREATE CATALOG IF NOT EXISTS lakehousecat")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS lakehousecat.deltadb;")
spark.sql(f"""CREATE VOLUME IF NOT EXISTS lakehousecat.deltadb.datalake;""")
spark.sql(f"""CREATE VOLUME IF NOT EXISTS lakehousecat.deltadb.delta_target_volume1;""")
spark.sql(f"""CREATE VOLUME IF NOT EXISTS lakehousecat.deltadb.delta_source_volume2;""")

# COMMAND ----------

# MAGIC %md
# MAGIC ####1. Write data into delta file (Datalake) and table (Lakehouse)

# COMMAND ----------

# read file
df = spark.read.csv('/Volumes/lakehousecat/deltadb/datalake/druginfo.csv',header=True,inferSchema=True)#Reading normal data from datalake

#write file(delta format)
df.write.format("delta").mode("overwrite").save("/Volumes/lakehousecat/deltadb/delta_target_volume1/")#writing normal data from deltalake(datalake) and writing as a delta file.

#write file(parquet format)
df.write.format("parquet").mode("overwrite").save("/Volumes/lakehousecat/deltadb/delta_source_volume2/")#writing normal data from parquet(datalake) and writing as a parquet(normal) file/not a delta file.

#writing as table(default delta table)
df.write.option("mergeSchema","True").saveAsTable("lakehousecat.deltadb.drugtargettable1",mode='overwrite')#writing normal data from deltalakehouse(lakehouse)
#behind it stores the data in deltafile format in the s3 bucket (location is hidden for us in databricks free edition)

# COMMAND ----------

# MAGIC %md
# MAGIC ####2. DML Operations in Delta Tables & Files
# MAGIC Support for DELETE/UPDATE/MERGE

# COMMAND ----------

# MAGIC %sql
# MAGIC use lakehousecat.deltadb

# COMMAND ----------

# MAGIC %sql
# MAGIC DESC HISTORY lakehousecat.deltadb.drugtargettable1

# COMMAND ----------

# MAGIC %sql
# MAGIC --DQL is supported
# MAGIC SELECT * FROM drugtargettable1 where uniqueid=163740;

# COMMAND ----------

# MAGIC %md
# MAGIC #####a. Table Update

# COMMAND ----------

# MAGIC %sql
# MAGIC --DML - update is possible in the delta tables/files
# MAGIC UPDATE drugtargettable1
# MAGIC   SET rating=rating-1
# MAGIC where uniqueid=163740;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESC HISTORY drugtargettable1

# COMMAND ----------

# MAGIC %sql
# MAGIC DESC DETAIL drugtargettable1 ;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM drugtargettable1 
# MAGIC where uniqueid=163740;

# COMMAND ----------

# MAGIC %md
# MAGIC #####b. Table Delete

# COMMAND ----------

# MAGIC %sql
# MAGIC --DML - Delete is possible on delta tables/files
# MAGIC DELETE FROM drugtargettable1
# MAGIC where uniqueid=163740;

# COMMAND ----------

# MAGIC %sql
# MAGIC desc history drugtargettable1

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM drugtargettable1
# MAGIC where uniqueid in (163740,206473);

# COMMAND ----------

# MAGIC %sql
# MAGIC desc history drugtargettable1;

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from drugtargettable1 version as of 1 where uniqueid in (163740,206473);

# COMMAND ----------

# MAGIC %md
# MAGIC #####c. File DML (Update/Delete)
# MAGIC We don't do file DML usually, we are doing here just for learning about 
# MAGIC - file also can be undergone with limited DML operation
# MAGIC - we need to learn about how the background delta operation is happening when i do DML

# COMMAND ----------

spark.read.format('delta').load('/Volumes/lakehousecat/deltadb/delta_target_volume1/').where('uniqueid=163740').show()

# COMMAND ----------

#DML on Files: How to update delta files
from delta.tables import DeltaTable
deltafile = DeltaTable.forPath(spark, "/Volumes/lakehousecat/deltadb/delta_target_volume1/")
deltafile.update("uniqueid=163740", { "rating": "rating - 1" } )

# COMMAND ----------

spark.read.format('delta').load('/Volumes/lakehousecat/deltadb/delta_target_volume1/').where('uniqueid=163740').show()

# COMMAND ----------

# MAGIC %md
# MAGIC #####d. File Delete

# COMMAND ----------

df=spark.read.format("delta").load('/Volumes/lakehousecat/deltadb/delta_target_volume1/')
df.where('uniqueid=206473').show()

# COMMAND ----------

from delta.tables import DeltaTable
deltaTable = DeltaTable.forPath(spark, "/Volumes/lakehousecat/deltadb/delta_target_volume1/")
deltaTable.delete("uniqueid=206473")

# COMMAND ----------

df=spark.read.format("delta").load('/Volumes/lakehousecat/deltadb/delta_target_volume1/')
df.where('uniqueid=206473').show()

# COMMAND ----------

# MAGIC %md
# MAGIC #####d. Merge Operation

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(*) from drugtargettable1;

# COMMAND ----------

# MAGIC %sql
# MAGIC --CTAS (Create table As Select)
# MAGIC create or replace table drugtargettable1_merge as select * from drugtargettable1 where rating<=8;

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from drugtargettable1_merge where uniqueid=6;

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(*) from drugtargettable1_merge;

# COMMAND ----------

# MAGIC %sql
# MAGIC --Delta table support merge operation for (insert/update/delete)
# MAGIC --2899 updated
# MAGIC --2801 inserted
# MAGIC MERGE INTO drugtargettable1_merge tgt
# MAGIC USING drugtargettable1 src
# MAGIC ON tgt.uniqueid = src.uniqueid
# MAGIC WHEN MATCHED THEN
# MAGIC   UPDATE SET tgt.usefulcount= src.usefulcount,
# MAGIC              tgt.drugname = src.drugname,
# MAGIC              tgt.condition = src.condition
# MAGIC WHEN NOT MATCHED
# MAGIC   THEN INSERT (uniqueid,rating,date,usefulcount, drugname, condition ) VALUES (uniqueid,rating,date,usefulcount, drugname, condition);

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from drugtargettable1_merge where rating<=8;

# COMMAND ----------

# MAGIC %sql
# MAGIC --After the below insert, Again try the merge in the above cell
# MAGIC insert into drugtargettable1_merge select 99999999,drugname,condition,rating,date,usefulcount 
# MAGIC from drugtargettable1 limit 1;

# COMMAND ----------

# MAGIC %sql
# MAGIC --Delta table support merge operation for (delete)
# MAGIC --1 deleted (which is not present in the source (source system deleted it already, hence target also has to delete))
# MAGIC MERGE INTO drugtargettable1_merge tgt
# MAGIC USING drugtargettable1 src
# MAGIC ON tgt.uniqueid = src.uniqueid
# MAGIC WHEN MATCHED THEN
# MAGIC   UPDATE SET tgt.usefulcount= src.usefulcount,
# MAGIC              tgt.drugname = src.drugname,
# MAGIC              tgt.condition = src.condition          
# MAGIC WHEN NOT MATCHED
# MAGIC   THEN INSERT (uniqueid,rating,date,usefulcount, drugname, condition ) VALUES (uniqueid,rating,date,usefulcount, drugname, condition)
# MAGIC WHEN NOT MATCHED BY SOURCE 
# MAGIC THEN DELETE;

# COMMAND ----------

#Merge operation using spark with (library delta.tables.DeltaTable) DSL (not by using SQL) - SQL is better to use
from delta.tables import DeltaTable
print(spark.read.table("drugtargettable1").count())
print(spark.read.table("drugtargettable1_merge").count())
tgt = DeltaTable.forName(spark, "drugtargettable1_merge")
src = spark.table("drugtargettable1")
(
    tgt.alias("tgt")
    .merge(
        src.alias("src"),
        "tgt.uniqueid = src.uniqueid"
    )
    .whenMatchedUpdate(set={
        "usefulcount": "src.usefulcount",
        "drugname": "src.drugname",
        "condition": "src.condition"
    })
    .whenNotMatchedInsert(values={
        "uniqueid": "src.uniqueid",
        "rating": "src.rating",
        "date": "src.date",
        "usefulcount": "src.usefulcount",
        "drugname": "src.drugname",
        "condition": "src.condition"
    })
    .whenNotMatchedBySourceDelete()
    .execute()
)


# COMMAND ----------

print(spark.read.table("drugtargettable1").count())
print(spark.read.table("drugtargettable1_merge").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ####3. Operations on Deltalake & Deltatables

# COMMAND ----------

# MAGIC %md
# MAGIC #####a. History & Versioning
# MAGIC *History* returns one row per commit/version and tells you what changed, when, and how.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESC HISTORY drugtargettable1_merge

# COMMAND ----------

# MAGIC %md
# MAGIC *Version as of* will reads the snapshot of drugtargettable1_merge at version 4 and Ignores all changes made in versions 5, 6, … current

# COMMAND ----------

# MAGIC %sql
# MAGIC --select * from (select * from deltadb.drugs version as of 2) where uniqueid=163740;
# MAGIC SELECT count(1) FROM drugtargettable1_merge VERSION AS OF 3;

# COMMAND ----------

# MAGIC %md
# MAGIC #####b. Time Travel
# MAGIC *Timestamp as of* Reads the table as it existed at that exact timestamp and Any commits after the given timestamp is ignored

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(1) FROM drugtargettable1_merge TIMESTAMP AS OF '2026-01-25T18:25:04.000+00:00';

# COMMAND ----------

# MAGIC %md
# MAGIC #####c. Vaccum
# MAGIC *VACUUM* in Delta Lake removes old, unused files to free up storage, default retention hours is 168. These files come from operations like DELETE, UPDATE, or MERGE and are kept temporarily so time-travel queries can work.

# COMMAND ----------

# MAGIC %sql
# MAGIC use lakehousecat.deltadb;
# MAGIC DESC HISTORY drugtargettable1_merge;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(1) FROM drugtargettable1_merge TIMESTAMP AS OF '2026-01-26T17:04:07.001+00:00';

# COMMAND ----------

# MAGIC %sql
# MAGIC --SET spark.databricks.delta.retentionDurationCheck.enabled = false;
# MAGIC --alter table drugtargettable1_merge SET TBLPROPERTIES ('delta.deletedFileRetentionDuration' = '24 hours');

# COMMAND ----------

# MAGIC %sql
# MAGIC VACUUM drugtargettable1_merge RETAIN 168 HOURS;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(1) FROM drugtargettable1_merge TIMESTAMP AS OF '2026-01-26T16:55:40.000+00:00';

# COMMAND ----------

spark.sql("VACUUM drugtargettable1_merge RETAIN 168 HOURS")

# COMMAND ----------

# MAGIC %sql
# MAGIC DESC HISTORY drugtargettable1_merge

# COMMAND ----------

# MAGIC %md
# MAGIC #####d. ACID Transactions
# MAGIC **Delta Lake uses ACID transactions under the hood via a transaction log.**
# MAGIC | ACID        | In Databricks         |
# MAGIC | ----------- | --------------------- |
# MAGIC | Atomicity   | Individual Transactions |
# MAGIC | Consistency | Schema + constraints  |
# MAGIC | Isolation   | Snapshot isolation    |
# MAGIC | Durability  | Transaction log       |

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE acid_demo_txn (
# MAGIC   id INT,
# MAGIC   amount INT
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO acid_demo_txn VALUES
# MAGIC (1, 100),
# MAGIC (2, 200),
# MAGIC (3, 300);

# COMMAND ----------

# MAGIC %sql
# MAGIC --Atomicity ()
# MAGIC UPDATE acid_demo_txn SET amount = amount + 100 WHERE id = 1;
# MAGIC UPDATE acid_demo_txn SET amount = amount + 200 WHERE id = 1;
# MAGIC describe history acid_demo_txn;

# COMMAND ----------

# MAGIC %sql
# MAGIC --Apply constraint for consistancy
# MAGIC ALTER TABLE acid_demo_txn
# MAGIC ADD CONSTRAINT positive_amount CHECK (amount > 0);
# MAGIC INSERT INTO acid_demo_txn VALUES (4, -500);

# COMMAND ----------

# MAGIC %sql
# MAGIC --Isolation
# MAGIC --Notebook1 (We can see the data in notebook1)
# MAGIC BEGIN TRANSACTION;
# MAGIC UPDATE acid_demo_txn SET amount = 999 WHERE id = 2;
# MAGIC --Notebook2 (We can see the data in notebook2 )

# COMMAND ----------

# MAGIC %sql
# MAGIC --Durability (Despite of terminate and starting back the serverless, data still survives durably)
# MAGIC INSERT INTO acid_demo_txn VALUES (5, 500);
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC #####e. Transactions Control using restore

# COMMAND ----------

# MAGIC
# MAGIC %sql
# MAGIC --select count(1) from deltadb.drugs where date>'2012-02-28';
# MAGIC --4329
# MAGIC delete from drugtargettable1 where date>'2012-02-28';

# COMMAND ----------

# MAGIC %sql
# MAGIC describe history drugtargettable1;

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1) from drugtargettable1;

# COMMAND ----------

# MAGIC %sql
# MAGIC RESTORE TABLE drugtargettable1 TO VERSION AS OF 0;

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1) from drugtargettable1;

# COMMAND ----------

# MAGIC %sql
# MAGIC RESTORE TABLE drugtargettable1 TO VERSION AS OF 0;

# COMMAND ----------

# MAGIC %sql
# MAGIC describe history drugtargettable1;

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1) from drugtargettable1;
