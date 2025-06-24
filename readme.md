# 🚀 AGORA Development Environment – Full Setup Guide

This guide is designed for new developers joining the AGORA project. It covers setting up the Python backend, dependency management, building API and GeoServer containers, and running everything with Docker Compose in both dev and production modes.

---

## 📚 1. Python API & Dependency Management

AGORA's API is based on Python 3.10 using **Poetry** and **Conda** for dependency management.

### 📦 Poetry (Recommended)

```bash
poetry add --lock package_name
poetry update
```

* Automatically updates `pyproject.toml` and `poetry.lock`

### 🐍 Conda (for system-level or pip-incompatible packages)

```bash
conda install some_package=version
conda env export --from-history > environment.yml
conda-lock -f environment.yml --lockfile conda-lock.yml
```

> Always run the image update script after changes:

```bash
./src/docker-python-env/create_docker_image.sh
```

---

## 🧱 2. How the `agora-api-image:latest` is Created

### 🔁 Automatic Image Update Script

**Path:**

```bash
./src/docker-python-env/create_docker_image.sh
```

**Logic:**

```bash
if git diff --exit-code pyproject.toml environment.yml; then
  echo "No changes in dependencies. Skipping image update."
  exit 0
else
  docker commit agora-dev-api agora-api-image:latest
fi
```

This script ensures that the Docker image is updated only when library dependencies change. All developers and CI pipelines should use this.

---

## 🌍 3. GeoServer Container Setup

AGORA uses a modular GeoServer build system with plugin support and custom CORS configuration.

### 📁 Structure

```
geoserver_agora/
├── plugins/                  # Plugin jars
├── Dockerfile                # Final image using base + plugins
├── download_plugins.sh

geoserver_base/
├── Dockerfile                # Base image
├── entrypoint.sh             # Startup logic
├── production_web.xml        # CORS etc.
├── set_geoserver_auth.sh     # Admin credentials
├── tasks.py                  # (Optional)
```

### 🏗 1. Build Base Image

```bash
cd geoserver_base/
docker build -t dcs-base-geoserver:2.24.4 .
```

### 📦 2. Download Plugins

```bash
cd geoserver_agora/
chmod +x download_plugins.sh
./download_plugins.sh "2.24.4" "mbstyle vectortiles"
```

> ⚠️ Warning: `plugins/` will be wiped before downloading.

### 🚀 3. Build AGORA GeoServer Image

```bash
docker build . -t agora-geoserver:2.24.4
```

---

## 🐳 4. Dev Image: Building & Running

To build and run the full dev environment:

```bash
chmod +x build_dev_container.sh
./build_dev_container.sh
```

Which runs:

```bash
docker compose -f docker-compose-dev.yml --env-file src/app/.env up -d --build
```

### ⚠️ Reminder

If you make any changes to dependencies in the API (`pyproject.toml` or `environment.yml`), you must run:

```bash
./src/docker-python-env/create_docker_image.sh
```

This ensures the dev image reflects those changes.

---

## ⚙️ 5. Docker Compose (Dev & Prod)

### 🔧 Dev Mode

```bash
docker compose -f docker-compose-dev.yml --env-file src/app/.env up -d
```

### 🚀 Production Mode

```bash
docker compose -f docker-compose-prod.yml --env-file src/app/.env up -d
```

### 📁 Example `.env`

```env
DATABASE_HOSTNAME=db
DATABASE_PORT=5432
DATABASE_NAME=agora
DATABASE_USERNAME=agora
DATABASE_PASSWORD=agora

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=760
REFRESH_TOKEN_EXPIRE_MINUTES=1000

GEOSERVER_ADMIN_USER=admin
GEOSERVER_ADMIN_PASSWORD=geoserver2
GEOSERVER_PORT=8383
GEOSERVER_CORS_ENABLED=True
GEOSERVER_CORS_ALLOWED_ORIGINS=*
GEOSERVER_CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,HEAD,OPTIONS
GEOSERVER_CORS_ALLOWED_HEADERS=*
GEOSERVER_CSRF_DISABLED=true
```

---

## 📁 6. API Code Structure

```
app/
├── auth/         # Login, Register, Token
├── db/           # SQLAlchemy + GeoAlchemy2 models
├── geoserver/    # GeoServer REST API integration
├── ligfinder/    # Spatial analysis module
├── utils/        # Shared helpers
└── main.py       # FastAPI entry point
```

---

## 🧪 7. Dev Utilities

* Enter API container:

```bash
docker exec -it agora-dev-api bash
```

* Restart only the API:

```bash
docker compose restart api
```

* Tail logs:

```bash
docker logs -f agora-dev-api
```

---

## ✅ 8. Production Deployment Note

In production, the API container directly mounts the `src/` directory from the main repository.

> **To reflect new changes, you must log into the production server and run:**
>
> ```bash
> git pull
> ```
>
> This ensures the latest codebase is updated inside the container.
> Since the container uses the mounted `src/` folder directly, no rebuild is required after pulling updates. Just make sure to test changes in dev before pushing to production..

> **This means any changes pushed to the `src/` codebase on the server are immediately reflected in production.** No rebuild is required for logic changes. Be careful and always test on dev first.
