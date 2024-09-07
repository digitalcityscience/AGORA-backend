echo "Building the TOSCA project's containers 🏗️"
docker-compose -f docker-compose-prod.yml --env-file src/app/.env build
echo "Containers built successfully. ✅" 

echo "Starting the TOSCA project's containers 🚀"
docker-compose -f docker-compose-prod.yml --env-file src/app/.env up -d

