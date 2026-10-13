# Rollout: static.piinro.place on Nekoweb, super.piinro.place on the VPS

## Host routing

| Host | Served by |
|---|---|
| `piinro.place` and `www.piinro.place` | Redirect to `https://static.piinro.place`, preserving the path and query |
| `static.piinro.place` | Nekoweb custom domain; serves the static frontend |
| `super.piinro.place` | VPS Nginx to Gunicorn/FastAPI |

The backend currently exposes `GET /api/health`. Post detail pages and `/feed.xml` are not implemented in this checkout yet; add their handlers before relying on those URLs.

## 1. Repository changes

- Nginx redirects the apex and `www` hosts to the static homepage and proxies `super.piinro.place` to the backend.
- FastAPI no longer serves the static frontend. CORS permits browser requests from `https://static.piinro.place`.
- The Nekoweb deploy workflow targets `static.piinro.place`; old self-links point to the custom domain or use relative paths.
- When post pages and RSS are implemented, serve them from `super.piinro.place`, use absolute `https://super.piinro.place/posts/<id>` feed links, and make frontend API calls to `https://super.piinro.place/api/...`.
- Add canonical links using `https://static.piinro.place/<path>` on static pages and `https://super.piinro.place/posts/<id>` on dynamic post pages.
- Once `/feed.xml` exists, add an RSS alternate link on static pages pointing to `https://super.piinro.place/feed.xml`.
- Nekoweb's custom-domain mapping serves the site directly at `static.piinro.place`; no redirect or proxy through the VPS is needed for that host.

## 2. One-time setup outside git

1. **Nekoweb:** add `static.piinro.place` as the custom domain and note the exact DNS target or records Nekoweb provides. Keep publishing the static frontend through the repository's Nekoweb workflow.
2. **DNS:** create these records at your DNS provider, substituting your actual VPS address and Nekoweb's provided target:

   | Type | Name | Value |
   |---|---|---|
   | `A` | `@` | VPS public IPv4 address |
   | `AAAA` | `@` | VPS public IPv6 address, only if configured |
   | `CNAME` | `www` | `piinro.place` (or use the same VPS A/AAAA records if CNAME is unavailable) |
   | `A` | `super` | VPS public IPv4 address |
   | `AAAA` | `super` | VPS public IPv6 address, only if configured |
   | As instructed by Nekoweb | `static` | Nekoweb's exact custom-domain target; do not point this at the VPS |

   The apex and `www` records reach Nginx only for its redirect to the static homepage. `static` resolves directly to Nekoweb, while `super` resolves to the VPS for the backend. DNS itself does not perform the apex redirect. If you want even apex/`www` traffic to bypass the VPS, use your DNS provider's separate URL-forwarding feature instead of the Nginx redirect. Lower TTLs before switching records.
3. **VPS firewall:** allow 22, 80, and 443.
4. **Certificate:** the VPS certificate must cover `piinro.place`, `www.piinro.place`, and `super.piinro.place` before enabling the HTTPS Nginx servers:
   ```bash
   sudo mkdir -p /var/www/certbot
   sudo certbot certonly --webroot -w /var/www/certbot -d piinro.place -d www.piinro.place -d super.piinro.place
   ```

## 3. Deploy on the VPS

### Before connecting

The VPS deploy script only deploys `master`: it fetches and checks out `master`, fast-forwards from `origin/master`, updates the frontend submodule, syncs dependencies, and restarts the systemd service. Before running it, commit and push the backend/Nginx changes to `master`. If the frontend submodule has changes, commit and push those from inside the submodule first, then commit and push the updated submodule reference in this repository.

### First-time VPS setup

Do this once if the VPS does not already have the service installed. The commands below assume the checkout and systemd unit use `/home/personal-site/personal-site-backend`, as configured in `deploy/systemd/personal-site-backend.service`.

1. Make sure DNS has propagated and the VPS firewall allows ports 22, 80, and 443. The `static` hostname should resolve to Nekoweb; `super` and, with the Nginx redirect setup, the apex and `www` should resolve to the VPS.
2. Install the required packages and create the service account/checkout, following the initial setup in `deploy/README.md`. Ensure the `personal-site` user can read the checkout and run `uv`.
3. Obtain the certificate before installing the HTTPS Nginx configuration. Since that configuration references certificate files, first create `/etc/nginx/sites-available/personal-site.conf` with this temporary HTTP-only config, enable it, and reload Nginx:

   ```nginx
   server {
      listen 80;
      server_name piinro.place www.piinro.place super.piinro.place;

      location /.well-known/acme-challenge/ {
         root /var/www/certbot;
      }

      location / {
         return 404;
      }
   }
   ```

   ```bash
   sudo mkdir -p /var/www/certbot
   sudo ln -s /etc/nginx/sites-available/personal-site.conf /etc/nginx/sites-enabled/personal-site.conf
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot certonly --webroot -w /var/www/certbot --cert-name piinro.place -d piinro.place -d www.piinro.place -d super.piinro.place
   ```

4. Install the service unit, run the first backend deploy, and enable the full Nginx configuration:

   ```bash
   cd /home/personal-site/personal-site-backend
   sudo cp deploy/systemd/personal-site-backend.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now personal-site-backend
   sudo ./scripts/deploy.sh
   sudo cp deploy/nginx/personal-site.conf /etc/nginx/sites-available/personal-site.conf
   sudo nginx -t && sudo systemctl reload nginx
   ```

   The enabled symlink continues to point at the same file when the temporary config is replaced by the full config. If you already have an enabled site, skip creating the symlink and removing the default site; copy the config, test it, and reload Nginx.

### Subsequent deployments

After changes have been pushed to `master`, run:

```bash
ssh <vps>
cd /home/personal-site/personal-site-backend
sudo ./scripts/deploy.sh
```

The deploy script restarts FastAPI but does not install or reload Nginx. When its configuration changes, run:

```bash
sudo cp deploy/nginx/personal-site.conf /etc/nginx/sites-available/personal-site.conf
sudo nginx -t && sudo systemctl reload nginx
```

For service or Nginx troubleshooting, check `sudo systemctl status personal-site-backend`, `sudo journalctl -u personal-site-backend -n 100 --no-pager`, and `sudo nginx -t`.

## 4. Verify

```bash
curl -I https://piinro.place/                 # redirects to static.piinro.place/
curl -I https://static.piinro.place/          # Nekoweb static homepage
curl https://super.piinro.place/api/health    # VPS FastAPI
sudo journalctl -u personal-site-backend -f
```

After implementing post pages and RSS, also verify `/posts/<id>` and `/feed.xml` on `super.piinro.place`.

Rollback: restore the previous repository version on the VPS, run `sudo ./scripts/deploy.sh`, and restore the previous Nginx configuration if necessary.
