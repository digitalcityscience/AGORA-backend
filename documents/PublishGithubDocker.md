## Publish Docker in Github

docker login --username orttak --password XXX ghcr.io
docker image ls
docker -t ligfinder_refactor_api:latest ghcr.io/orttak/apitest:fromlocal
docker tag ligfinder_refactor_api:latest ghcr.io/orttak/apitest:fromlocal
docker push ghcr.io/orttak/apitest:fromlocal
