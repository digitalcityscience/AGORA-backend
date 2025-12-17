#!/bin/sh 

GEOSERVER_CONTAINER_NAME=$1
FILENAME=$2

echo Filename to restore: $FILENAME

BACKUP_TAR_PATH="geoserver_backup/${FILENAME}.tar.gz"
echo Backup tar path: $BACKUP_TAR_PATH
mkdir -p geoserver_backup/temp
tar -xzf ${BACKUP_TAR_PATH} -C geoserver_backup/temp

docker cp geoserver_backup/temp/data ${GEOSERVER_CONTAINER_NAME}:/geoserver_data

rm -rf geoserver_backup/temp

docker stop ${GEOSERVER_CONTAINER_NAME}
docker start ${GEOSERVER_CONTAINER_NAME}