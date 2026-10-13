# Deployment

These templates assume the repository is deployed to `/home/personal-site/personal-site-backend` and the domain is replaced in `nginx/personal-site.conf`.

## Initial VPS setup

Install the system packages required by the service:

```bash
sudo apt update
sudo apt install -y nginx git python3 python3-venv certbot python3-certbot-nginx
```

Create the service account and checkout the repository with its frontend submodule:

```bash
sudo useradd --system --create-home --home-dir /var/www/personal-site --shell /usr/sbin/nologin personal-site
sudo -u personal-site git clone --recurse-submodules <backend-repository-url> /home/personal-site/personal-site-backend
cd /home/personal-site/personal-site-backend
sudo -u personal-site uv sync --no-dev
```

If `uv` is not installed for the service account, install it according to the official uv instructions or create the virtual environment with the system Python and install the project dependencies there.

## Install systemd and Nginx configuration

```bash
sudo cp deploy/systemd/personal-site-backend.service /etc/systemd/system/
sudo cp deploy/nginx/personal-site.conf /etc/nginx/sites-available/personal-site.conf
sudo ln -s /etc/nginx/sites-available/personal-site.conf /etc/nginx/sites-enabled/personal-site.conf
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

## Deploy updates

Run the deployment script as root from the checked-out repository:

```bash
sudo ./scripts/deploy.sh
```

The script fast-forwards the checkout to `origin/master`, updates the frontend submodule, syncs production dependencies, and restarts `personal-site-backend`. It refuses to overwrite local changes because it uses `git pull --ff-only`.

## GitHub Actions deploy

`.github/workflows/deploy-backend.yml` deploys after pushes to `master`; it can also be run manually with `workflow_dispatch`. It connects over SSH and invokes the existing deploy script. It does not copy or reload Nginx configuration; apply Nginx changes manually using the commands above.

Use a dedicated SSH account instead of storing the root SSH key in GitHub. On the VPS, create `personal-site-deploy`, add its public key to `/home/personal-site-deploy/.ssh/authorized_keys`, and allow it to run only the fixed deploy command without a password:

```bash
sudo adduser --disabled-password --gecos "" personal-site-deploy
sudo install -d -o personal-site-deploy -g personal-site-deploy -m 700 /home/personal-site-deploy/.ssh
sudoedit /home/personal-site-deploy/.ssh/authorized_keys
sudo chown personal-site-deploy:personal-site-deploy /home/personal-site-deploy/.ssh/authorized_keys
sudo chmod 600 /home/personal-site-deploy/.ssh/authorized_keys
printf '%s\n' 'personal-site-deploy ALL=(root) NOPASSWD: /usr/bin/bash /home/personal-site/personal-site-backend/scripts/deploy.sh' | sudo tee /etc/sudoers.d/personal-site-deploy
sudo chmod 440 /etc/sudoers.d/personal-site-deploy
sudo visudo -cf /etc/sudoers.d/personal-site-deploy
```

Generate a dedicated Ed25519 key pair on a trusted computer. Add the `.pub` key to `authorized_keys`; never upload or commit the private key:

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\personal-site-actions" -C github-actions-personal-site
```

Leave the key passphrase empty so the non-interactive runner can use it. Protect the `master` branch and require review for workflow/deploy changes: a push to `master` can deploy production code.

In the GitHub repository, add these Actions secrets under **Settings > Secrets and variables > Actions**:

| Secret | Value |
|---|---|
| `VPS_HOST` | VPS IP address or SSH hostname, without a username |
| `VPS_USER` | `personal-site-deploy` |
| `VPS_SSH_PRIVATE_KEY` | Contents of the private key file, `personal-site-actions` |
| `VPS_KNOWN_HOSTS` | Pinned SSH host-key line(s) for the VPS |

Obtain host keys with `ssh-keyscan -H <VPS_HOST>`, but verify the fingerprint against the VPS console before saving its output as `VPS_KNOWN_HOSTS`. The workflow rejects unknown or changed host keys. Once these are set and this workflow is pushed to `master`, each push to `master` triggers a deploy; use **Actions > Deploy backend to VPS > Run workflow** for a manual deploy.