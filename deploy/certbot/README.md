# TLS and DNS setup

Replace `example.com` and `www.example.com` in the Nginx configuration with the real domain names.

## DNS records

Create DNS records at the DNS provider:

- `A` record for the domain pointing to the VPS public IPv4 address.
- `A` record for `www` pointing to the VPS public IPv4 address, if `www` is used.
- `AAAA` records only if the VPS has a working public IPv6 address.

Wait for DNS to resolve before requesting a certificate:

```bash
dig +short example.com
dig +short www.example.com
```

## HTTP-01 certificate

The included Nginx configuration exposes the ACME challenge directory. Install Certbot and the Nginx plugin on the VPS, then run:

```bash
sudo mkdir -p /var/www/certbot
sudo certbot --nginx -d example.com -d www.example.com
```

Certbot will update the live Nginx configuration and install its renewal timer. Test renewal with:

```bash
sudo certbot renew --dry-run
```

## DNS-01 certificate

Use DNS-01 when the site needs wildcard certificates or port 80 cannot be exposed. The Certbot plugin depends on the DNS provider. For example, a provider plugin generally uses a command shaped like:

```bash
sudo certbot certonly \
    --dns-PROVIDER \
    --dns-PROVIDER-credentials /root/.secrets/certbot/provider.ini \
    -d example.com \
    -d '*.example.com'
```

Replace `PROVIDER` with the actual Certbot plugin for the DNS provider. Do not commit the credentials file; restrict it with `sudo chmod 600`.