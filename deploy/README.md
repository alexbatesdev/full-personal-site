# Deployment

These templates assume the repository is deployed to `/var/www/personal-site-backend` and the domain is replaced in `nginx/personal-site.conf`.

## Initial VPS setup

Install the system packages required by the service:

```bash
sudo apt update
sudo apt install -y nginx git python3 python3-venv certbot python3-certbot-nginx
```

Create the service account and checkout the repository with its frontend submodule:

```bash
sudo useradd --system --create-home --home-dir /var/www/personal-site --shell /usr/sbin/nologin personal-site
sudo mkdir -p /var/www
sudo chown personal-site:personal-site /var/www/personal-site
sudo -u personal-site git clone --recurse-submodules <backend-repository-url> /var/www/personal-site-backend
cd /var/www/personal-site-backend
sudo -u personal-site uv sync --no-dev
```

If `uv` is not installed for the service account, install it according to the official uv instructions or create the virtual environment with the system Python and install the project dependencies there.

## Install systemd and Nginx configuration

```bash
sudo cp deploy/systemd/personal-site-backend.service /etc/systemd/system/
sudo cp deploy/nginx/personal-site.conf /etc/nginx/sites-available/personal-site
sudo ln -s /etc/nginx/sites-available/personal-site /etc/nginx/sites-enabled/personal-site
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now personal-site-backend
sudo systemctl reload nginx
```

Before enabling Nginx, replace `example.com` and the certificate paths in the site configuration. The HTTP-only portion can be enabled first to obtain a certificate; Certbot details are in `certbot/README.md`.

## Service operations

```bash
sudo systemctl status personal-site-backend
sudo journalctl -u personal-site-backend -f
sudo systemctl restart personal-site-backend
```

The unit uses `Restart=on-failure`, so systemd restarts the service after an unexpected process exit.