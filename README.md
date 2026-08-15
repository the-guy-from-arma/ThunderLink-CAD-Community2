# ThunderLink CAD — Community 2

This repository is the isolated CAD 2 application. It is a separate community
from Faircroft/CAD 1 and must be deployed with its own Railway service, its own
PostgreSQL service, its own Arma Reforger identity, and its own secrets.

## Security boundary

- CAD 2 connects directly only to the PostgreSQL URL in `DATABASE_URL`.
- CAD 2 never connects to the CAD 1 database or imports the CAD 1 service.
- CAD 2 never receives `FCX_DATABASE_URL` and never connects to the FCX database.
- Ravenhood requests go to FCX-Control over authenticated HTTPS.
- FCX-Control calls CAD 2's authenticated settlement adapter when an FCX order
  needs to debit or credit this community's game bank.
- Global FCX, Ravenhood, and FEC administration stays in FCX-Control.

```text
CAD 2 app -> CAD 2 PostgreSQL
CAD 2 app -> FCX-Control API -> FCX PostgreSQL
FCX-Control -> CAD 2 settlement adapter -> CAD 2 game bank

CAD 2 -X-> CAD 1
CAD 2 -X-> FCX PostgreSQL
```

## Required Railway variables

```env
APP_DATABASE_ROLE=cad2
COMMUNITY_ID=community_2
DATABASE_URL=${{CAD2-Postgres.DATABASE_URL}}

ARMA_SERVER_ID=community-2-arma
ARMA_BRIDGE_API_KEY=<unique CAD 2 bridge secret>

FCX_API_URL=https://<fcx-control-domain>
FCX_COMMUNITY_ID=community_2
FCX_API_KEY=<credential issued by FCX-Control to community_2>
FCX_REMOTE_MARKET_ENABLED=true
FCX_GLOBAL_ADMIN_ENABLED=false
FCX_RUN_INTEGRATED_ENGINE=0

FCX_BANK_ADAPTER_ENABLED=true
FCX_BANK_SETTLEMENT_SECRET=<unique CAD 2 settlement secret>
SECRET_KEY=<unique CAD 2 session secret>
```

Do not add `FCX_DATABASE_URL`, a CAD 1 database URL, or CAD 1 Arma credentials
to this service.

## Start and health checks

Railway starts `python launch_service.py`. The launcher refuses to start when:

- the database role is not `cad2`;
- the community/server identity resembles CAD 1;
- the CAD 2 database cannot be reached;
- the FCX credential is not assigned to `COMMUNITY_ID`; or
- local/global FCX engine controls are enabled.

`GET /api/health` reports the CAD 2 database and FCX API separately without
exposing database names, hosts, credentials, or API keys.

## Local development

Copy `.env.example`, provide a local CAD 2 PostgreSQL database and a reachable
FCX-Control development service, then run:

```bash
docker compose up --build
```

The application listens on `http://localhost:8080`.
