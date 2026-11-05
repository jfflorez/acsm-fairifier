# Configuration

The app is configured with environment variables. All are optional: with none set, the app behaves as before (file upload, data in `<project>/data`, debug on).

| Variable | Default | Effect |
|---|---|---|
| `APP_SHARED_MODE` | `0` | `0`: users upload an HDF5 file with dash-uploader. `1`: users pick a file from the data folder (no upload). |
| `APP_DATA_DIR` | `data` | Data folder. Relative paths are resolved from the project root; absolute paths are used as is. In shared mode it is the folder listed in the file picker. In upload mode it is where uploaded files are saved. The folder must exist. |
| `DASH_DEBUG` | `1` | `1`: Dash debug mode on. `0`: off (use for shared deployments, e.g. Renku). |
| `DOCKER_CONTAINER` | unset | Set to any non-empty value inside Docker to skip opening a browser on startup. |

## Shared mode

Use it when JupyterLab and the app can both read the same folder. Set `APP_SHARED_MODE=1`, and the app lists the `.h5` / `.hdf5` files in `APP_DATA_DIR` instead of asking for an upload. Use the refresh button after adding files.

## Setting the variables

- **Development:** put them in a `.env` file at the project root (keep it out of git).
- **Deployment:** export them in the launch script, or set them in `docker run -e` or docker-compose.

On Windows, use forward slashes in paths (`data/raw`).