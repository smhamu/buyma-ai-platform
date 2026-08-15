# EU Product Research

## Brand seed

After applying database migrations, seed the initial luxury brand master from the backend container:

```sh
docker-compose --env-file .env.production -f docker-compose.prod.yml exec backend \
  python scripts/seed_luxury_brands.py
```

The command is idempotent. It creates only missing `brand_code` values and does not overwrite existing brand records. Hermès and CHANEL start with the conservative `research_only` policy. Other initial brands use `unknown`; an administrator must verify and update policies before relying on them for listing decisions.

Brand master mutations require an admin account. Authenticated users may list and view brands. Suppliers may carry multiple brands through `supplier_brands`; every product research candidate references exactly one Brand record.
