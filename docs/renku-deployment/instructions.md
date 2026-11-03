# Deploying acsm-fairifier on Renku

These instructions describe how to deploy the `acsm-fairifier` application on Renku through the `acsm-fairifier-workbench` project, configuring its computational environment and session launchers to make the application accessible and runnable by other users through a web browser.

## 1. Clone the repository
```bash
git clone https://github.com/jfflorez/acsm-fairifier
cd acsm-fairifier
```
Initialize the available submodule:

```bash
git submodule update --init dima
```

## 2. Build the Docker image
```bash
docker build -f Dockerfile.acsmchain.renku -t florezjf/acsm-fairifier-env:vX.Y.Z .
```

The Dockerfile creates the conda environments and copies
`docs/renku-deployment/renku-start.sh` to `/usr/local/bin/`.
Project code is NOT in the image; Renku clones it at session start.

Rebuild when the Dockerfile, environment files, or `renku-start.sh` change.
Code-only changes do not need a rebuild.

## 3. Test locally (recommended)
```bash
docker compose up
```

Open [http://localhost:8889/lab](http://localhost:8889/lab). Locally the container runs as root, so
the script needs `--ServerApp.allow_root=true`; Renku runs as UID 1000 and
does not. Remove or make that flag conditional before building the release image.

## 4. Push the image to Dockerhub

    docker login
    docker push florezjf/acsm-fairifier-env:vX.Y.Z

Use a new tag per release. The image is public, so Renku can pull it
without credentials.

## 5. Configure the Renku project

1. Create the project `acsm-fairifier-workbench`.
2. Add the git repo `https://github.com/jfflorez/acsm-fairifier` as a code repository.
3. Add a session launcher with a custom image:

| Setting | Value |
|---|---|
| Container image | `florezjf/acsm-fairifier-env:vX.Y.Z` |
| Default URL path | `/lab` |
| Port | `8888` |
| Working directory | `/workspace` |
| Mount directory | `/workspace` |
| UID / GID | `1000` / `1000` |
| Command | `["sh","-c"]` |
| Args | `["exec bash /usr/local/bin/renku-start.sh"]` |
| Strip session URL path prefix | No |

4. Launch a session.

## 6. Run the acsm-fairifier application using the Renku's Session Launcher

1. Renku pulls the image and starts the container as UID 1000.
2. Renku clones `acsm-fairifier` into `/workspace/acsm-fairifier`.
3. `renku-start.sh` runs: it `cd`s to `/workspace/$MAIN_REPO`, starts the
   Dash app in the background (if `app/data_flagging_app.py` exists), then
   `exec`s JupyterLab.
4. JupyterLab is served at `$RENKU_BASE_URL_PATH/lab`; Dash is reached
   through the jupyter-server-proxy named route (`/dash-app/`).

## 7. Releasing a change

| Change | Action |
|---|---|
| App code only | Commit and push; start a new session |
| Dockerfile, env files, start script | Rebuild, push a new tag, update the tag in the launcher |

## Troubleshooting

| Symptom | Check |
|---|---|
| Session won't start | Image tag exists on Docker Hub; session logs |
| "Dash skipped" in logs | Cloned folder name doesn't match `MAIN_REPO` |
| Permission errors on write | Target folder must be writable by UID 1000 |