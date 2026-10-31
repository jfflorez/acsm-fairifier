# Changing ACSM Fairifier data flow architecture

## 1. Current architecture

Currently, the Docker container runs two web applications:

- **JupyterLab**, listening internally on port `8888`.
- **Dash (Plotly)**, listening internally on port `8050`.

Both services are exposed to the host, allowing users to access them independently through their browsers.

```text
Browser
  |------------------> JupyterLab (8888)
  |
  |------------------> Dash / Plotly (8050)
```

## 2. Proposed architecture change

Expose a single host port for browser communication with JupyterLab and use **Jupyter Server Proxy** to forward requests to the Dash application running inside the same container.

```text
Browser
   |
   v
JupyterLab (8888)
   |
   | Jupyter Server Proxy
   v
Dash / Plotly (8050)
```

The browser accesses the Dash application through JupyterLab, without requiring a separate host-facing port.

The Docker Compose configuration is therefore simplified to expose only JupyterLab:

```yaml
ports:
  - "8889:8888"
```

Dash continues listening internally on port `8050`, but is no longer directly exposed to the host.

### Advantages

- **Reduced service exposure:** background web services such as Dash are accessed through Jupyter Server Proxy rather than exposed independently.
- **Unified access:** JupyterLab becomes the common entry point for notebooks, computational workflows and interactive applications.
- **Simplified deployment:** fewer exposed ports and a more integrated application architecture.
- **Improved maintainability:** additional services can potentially be integrated without exposing each one independently.

### Disadvantages

- Additional infrastructure configuration is required.
- Applications must account for the URL prefixes introduced by the proxy.
- Troubleshooting requires understanding the interaction between JupyterLab, Jupyter Server Proxy and the background applications.

## 3. Motivation and relevance for Renku deployment

This architectural change is part of preparing ACSM Fairifier for deployment on the **Renku platform**.

ACSM Fairifier relies on JupyterLab to orchestrate computational workflows and access additional background web services, such as the Dash-based data annotation tool. Integrating these services through Jupyter Server Proxy provides a unified access point while avoiding the need to expose each application through a separate host-facing port.

## 4. Implementation notes

I encountered some issues when integrating Jupyter Server Proxy with the Dash application. In particular, the Dash Uploader component did not pick up the intended configuration and instead fell back to its default values.

This was resolved by serving the application layout through a callable function, ensuring that the upload component is instantiated after the uploader configuration has been applied.

**Relevant documentation:**

- [Jupyter Server Proxy – Configuration and process proxying](https://jupyter-server-proxy.readthedocs.io/en/latest/server-process.html)
- [Dash Uploader – Configuration](https://github.com/fohrloop/dash-uploader). Check out doctrings in `dash_uploader/configure_upload.py`.  See `README.md`, i.e., *Example with callback (and other options)*.
- [Dash – App layout](https://dash.plotly.com/app-lifecycle#layout)


