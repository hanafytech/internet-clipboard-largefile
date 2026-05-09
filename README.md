# Internet Clipboard (Large File Edition) 📋

A heavy-duty, self-hosted, "burn-after-reading" pastebin designed to handle massive file transfers (up to 10GB) securely over a local network or reverse proxy.

Unlike the standard "RAM-only" version of Internet Clipboard, this edition streams large files directly to a mapped hard drive volume. The file is permanently deleted from the disk the exact millisecond the recipient finishes downloading it.

## ✨ Features
* **Massive Payloads:** Supports file uploads up to 10GB without crashing server RAM.
* **Burn-After-Reading:** Text messages are destroyed upon viewing. Files are destroyed immediately upon download.
* **Live Progress Bar:** Built-in animated progress bar to track massive network transfers.
* **Custom URLs:** You dictate the URL. Just navigate to `yourdomain.com/whatever-you-want`.
* **Modern Dark Theme:** A sleek, high-contrast dark UI that is easy on the eyes.

## ⚠️ Architectural Requirements
* **Reverse Proxy Required:** To support 10GB uploads, this application should be routed through a reverse proxy (like Nginx Proxy Manager) rather than Cloudflare Tunnels (which strictly cap uploads at 100MB).
* **Disk Space:** Ensure the host machine has enough physical storage space mapped to the `/data` volume to handle your maximum expected upload size.

## 🚀 Quick Start (Deploying via Docker Hub)

If you just want to run the application, you don't need to clone this repository. You can use the pre-built image from Docker Hub.

1. Create a folder for the app and make a `docker-compose.yml` file inside it:

```yaml
services:
  internet-clipboard-largefile:
    image: hanafytech/internet-clipboard-largefile:latest
    container_name: internet-clipboard-largefile
    restart: unless-stopped
    ports:
      - "8081:8080"
    volumes:
      - ./data:/data
```

2. Run the container:
```bash
docker compose up -d
```

## 🛠️ Local Development & Building from Source

If you want to modify the code or build the image yourself:

1. Clone the repository:
```bash
git clone [https://github.com/hanafytech/internet-clipboard-largefile.git](https://github.com/hanafytech/internet-clipboard-largefile.git)
cd internet-clipboard-largefile
```

2. Build and run using Docker Compose:
```bash
docker compose up -d --build
```

### Nginx Proxy Manager Configuration
If exposing this via Nginx Proxy Manager, you **must** add the following to the "Custom Nginx Configuration" under the Advanced tab of your Proxy Host to prevent Nginx from blocking or timing out the massive upload:

```nginx
client_max_body_size 10000M;
proxy_read_timeout 7200s;
proxy_connect_timeout 7200s;
proxy_send_timeout 7200s;
send_timeout 7200s;
```

## 💻 Tech Stack
* **Backend:** Python, Flask, Gunicorn (Configured for 2-hour timeouts)
* **Frontend:** HTML5, CSS3, Vanilla JS (XMLHttpRequest for progress tracking)
* **Containerization:** Docker
