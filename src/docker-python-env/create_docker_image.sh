if git diff --exit-code pyproject.toml environment.yml; then
    echo "No changes in pyproject.toml or environment.yml. Exiting."
    exit 0
else
    docker commit agora-dev-api  agora-api-image:latest
fi