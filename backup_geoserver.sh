#!/bin/sh 

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

GEOSERVER_CONTAINER_NAME=$1
BACKUP_DIR="geoserver_backup"
BACKUP_NAME="geoserver-backup-${TIMESTAMP}.tar.gz"
TEMP_DIR="${BACKUP_DIR}/temp-${TIMESTAMP}"

docker exec ${GEOSERVER_CONTAINER_NAME} tar -czf /tmp/geoserver_data_backup.tar.gz -C /geoserver_data .
docker cp ${GEOSERVER_CONTAINER_NAME}:/tmp/geoserver_data_backup.tar.gz ${BACKUP_DIR}/${BACKUP_NAME}
docker exec ${GEOSERVER_CONTAINER_NAME} rm /tmp/geoserver_data_backup.tar.gz
echo "Backup created: ${BACKUP_DIR}/${BACKUP_NAME}"