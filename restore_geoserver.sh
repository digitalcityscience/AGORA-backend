#!/bin/sh 

FILENAME=$1

echo Filename to restore: $FILENAME

BACKUP_TAR_PATH="geoserver_backup/${FILENAME}.tar.gz"
echo Backup tar path: $BACKUP_TAR_PATH
mkdir -p geoserver_backup/temp
tar -xzf ${BACKUP_TAR_PATH} -C geoserver_backup/temp

GEOSERVER_CONTAINER_NAME='agora-geoserver-dev-container'
docker cp geoserver_backup/temp/data ${GEOSERVER_CONTAINER_NAME}:/geoserver_data

rm -rf geoserver_backup/temp

docker stop ${GEOSERVER_CONTAINER_NAME}
docker start ${GEOSERVER_CONTAINER_NAME}