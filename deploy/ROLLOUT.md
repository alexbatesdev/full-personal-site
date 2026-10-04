# Rollout: piinro.place on the VPS with nekoweb as the static origin

Target: `piinro.place` resolves to the VPS. Nginx sends dynamic paths to gunicorn and proxies everything else to nekoweb (`origin.piinro.place`).

| Path | Served by |
|---|---|
| `/api/*` | VPS (FastAPI) |
| `/posts/<id>` (post detail page) | VPS |
| `/feed.xml` (RSS) | VPS |
| everything else (including `/posts/` assets) | nekoweb |

## 1. Changes made locally (via git)

1. **Nginx** (`deploy/nginx/personal-site.conf`)
   - Add explicit `location` blocks for `/api/`, `= /feed.xml` and `~ ^/posts/[0-9]+/?$` that proxy to `personal_site_backend`.
   - Change `location /` to `proxy_pass https://origin.piinro.place;` with `Host origin.piinro.place`, `proxy_ssl_server_name on`, and optional `proxy_cache`.
   - Add `/var/www/certbot` webroot handling if not already present.
2. **Backend** (`src/personal_site_backend`)
   - `api/routes/posts.py`: `post_page` currently declares `response_model=list[PostRead]` but returns a `FileResponse`. Remove the `response_model`.
   - Add `GET /feed.xml` that builds RSS from non-private posts with `post_to_rss=True`. Register it in `api/router.py`.
   - Use absolute post URLs (`https://piinro.place/posts/<id>`) in the feed.
   - `main.py`: the catch-all `StaticFiles` mount is only a fallback now. Keep it or remove it once nginx is routing.
   - Trust proxy headers: set `forwarded_allow_ips` in `deploy/gunicorn/gunicorn.conf.py` if the app builds absolute URLs from the request.
3. **Frontend**
   - Use relative URLs (`/api/...`) in the JS.
   - Add `<link rel="alternate" type="application/rss+xml" href="/feed.xml">` to the static pages.
   - Add `<link rel="canonical" href="https://piinro.place/<path>">` to each page, so search engines prefer the real domain over `piinro.nekoweb.org`.
   - Add a redirect script to the shared `<head>` so direct visits to `piinro.nekoweb.org` land on the real domain (the API and post routes only exist on the VPS):
     ```html
     <script>
       if (!["piinro.place", "localhost", "127.0.0.1"].includes(location.hostname)) {
         location.replace("https://piinro.place" + location.pathname + location.search + location.hash);
       }
     </script>
     ```
   - Search the frontend for hardcoded `piinro.nekoweb.org` URLs and make them relative.
4. Commit and push to `master`.

## 2. One-time setup outside git

1. **nekoweb:** add custom domain `origin.piinro.place` and follow its DNS instructions. Publish the static files there as usual.
2. **DNS:** point `piinro.place` and `www` (A/AAAA) at the VPS. Point `origin` at nekoweb. Lower the TTL beforehand.
3. **VPS firewall:** allow 22, 80 and 443.
4. **Certificate** on the VPS (before enabling the 443 block):
   ```bash
   sudo mkdir -p /var/www/certbot
   sudo certbot certonly --webroot -w /var/www/certbot -d piinro.place -d www.piinro.place
   ```

## 3. Pulling the changes on the VPS

```bash
ssh <vps>
cd /home/personal-site/personal-site-backend
sudo scripts/deploy.sh                 # pull, submodules, uv sync, restart backend
```

`deploy.sh` does not touch Nginx. When the Nginx config changed:

```bash
sudo cp deploy/nginx/personal-site.conf /etc/nginx/sites-available/personal-site
sudo nginx -t && sudo systemctl reload nginx
```

First time only, follow `deploy/README.md` (systemd unit, symlink in `sites-enabled`, remove the default site).

## 4. Verify

```bash
curl -I https://piinro.place/                 # content from nekoweb
curl https://piinro.place/api/health          # VPS
curl -I https://piinro.place/posts/1          # VPS, HTML
curl https://piinro.place/feed.xml            # VPS, valid RSS
sudo journalctl -u personal-site-backend -f
```

Rollback: `git checkout <previous-commit>` on the VPS and re-run `scripts/deploy.sh`. Point DNS back at nekoweb if the VPS is unusable.
