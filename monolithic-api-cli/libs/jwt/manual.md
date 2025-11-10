here’s a clean “shopping list” for Poetry so your JWT + PyNest + Strawberry/FastAPI GraphQL setup just works. i’ll give you a core set (works for prod/dev/local), plus an ultra-minimal HS256-only option for local if you really want no crypto wheels.

## Core runtime (recommended for **all** envs)

* `PyJWT[crypto]` — JWT with RSA/ECDSA/EdDSA support via `cryptography`. ([PyJWT][1])
* `pynest-api` — PyNest framework (DI + modules). ([PyPI][2])
* `strawberry-graphql[fastapi]` — GraphQL + FastAPI router (`GraphQLRouter`). ([Strawberry GraphQL][3])
* `fastapi` — web framework (PyNest is built on it). ([PyPI][4])
* `uvicorn[standard]` — ASGI server (adds uvloop/httptools/websockets for perf). ([PyPI][5])
* `python-dotenv` — load `.env` locally (nice for dev/local). ([PyPI][6])

**Poetry add (one-liners):**

```bash
poetry add "PyJWT[crypto]" pynest-api "strawberry-graphql[fastapi]" fastapi "uvicorn[standard]" python-dotenv
```

> Why these:
> • `PyJWT[crypto]` pulls `cryptography` so RS256/ES256/EdDSA just work. ([PyJWT][1])
> • Strawberry’s own docs say to install `strawberry-graphql[fastapi]` for the FastAPI integration. ([Strawberry GraphQL][3])
> • PyNest sits atop FastAPI, so keeping FastAPI/Uvicorn explicit avoids version mismatches and gives you a known ASGI server. ([PyPI][4])

---

## Minimal alt for **local HS256-only** (no asymmetric keys)

If you’re **only** using HS256 locally and want to skip crypto wheels:

```bash
poetry add PyJWT pynest-api "strawberry-graphql[fastapi]" fastapi "uvicorn[standard]" python-dotenv
```

(When you switch to RS256/ES256/EdDSA, upgrade to `PyJWT[crypto]` so `cryptography` is available.) ([PyJWT][1])

---

## Optional add-ons (use if you need them)

* `pytest` / `httpx` — testing utilities (if you plan JWT/GraphQL tests).
* `types-python-jwt` doesn’t exist; rely on inline typing. (PyJWT ships type hints.)
* If you’ll expose JWKS and do key math directly, `PyJWT[crypto]` already installs `cryptography` (no extra package needed). ([PyJWT][1])

---

## Quick pyproject snippet (for reference)

```toml
[tool.poetry.dependencies]
python = "^3.11"
PyJWT = { version = "^2", extras = ["crypto"] }
pynest-api = "^0.0.1"
strawberry-graphql = { version = "^0", extras = ["fastapi"] }
fastapi = "^0.115"
uvicorn = { version = "^0.30", extras = ["standard"] }
python-dotenv = "^1.0"
```

* Extras syntax in Poetry follows PEP 508 just like pip (e.g., `package[extra]`). ([ianwootten.co.uk][7])

---

### TL;DR

* **Install:** `poetry add "PyJWT[crypto]" pynest-api "strawberry-graphql[fastapi]" fastapi "uvicorn[standard]" python-dotenv`
* That’s enough to mint/verify/refresh JWTs (RS256/ES256/EdDSA or HS256), run your GraphQL API on FastAPI/Uvicorn, and load `.env`. ([PyJWT][1])

Want me to pin versions to what you already have in your lockfile or CI image?

[1]: https://pyjwt.readthedocs.io/en/stable/installation.html?utm_source=chatgpt.com "Installation — PyJWT 2.10.1 documentation - Read the Docs"
[2]: https://pypi.org/project/pynest-api/?utm_source=chatgpt.com "pynest-api"
[3]: https://strawberry.rocks/docs/integrations/fastapi?utm_source=chatgpt.com "FastAPI | 🍓 Strawberry GraphQL"
[4]: https://pypi.org/project/fastapi/?utm_source=chatgpt.com "fastapi"
[5]: https://pypi.org/project/uvicorn/?utm_source=chatgpt.com "uvicorn - PyPI"
[6]: https://pypi.org/project/python-dotenv/?utm_source=chatgpt.com "python-dotenv"
[7]: https://www.ianwootten.co.uk/2021/04/07/installing-module-extras-with-pipenv-and-poetry/?utm_source=chatgpt.com "Installing Module Extras with Pipenv and Poetry - Ian Wootten"


---

here’s the **minimum you need** to (1) generate, (2) validate, and (3) renew JWTs in your PyNest app—plus the **smallest .env** sets for **prod / dev / local**. I’ve kept it lean and aligned to PyJWT’s documented encode/decode behavior (issuer, audience, leeway, alg pinning) and the JWT/JWK RFCs. ([PyJWT][1])

---

# Minimal actions

## 0) Wire the module (once)

* Add `JwtModule` to your app/root module so `JwtService` and `JwtGuard` are injectable.
* That’s it—no business logic inside the module; it only registers providers (your pattern).

## 1) Generate (mint) tokens — **access + refresh**

Create a tiny class anywhere (e.g., `apps/auth/issue_tokens.py`) and call `JwtService`:

```python
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class IssueTokens:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    def run(self, user_id: str, uname: str, au: int):
        access = self.jwt.sign_access(
            sub=user_id,
            au=au,
            payload_overrides={"uname": uname},  # optional extras
        )
        refresh = self.jwt.sign_refresh(
            sub=user_id,
            au=au,
            payload_overrides={"sess": {"id": f"S-{user_id}"}},  # optional
        )
        return {"access": access, "refresh": refresh}
```

* PyJWT signs with the algorithm you pinned (e.g., RS256/ES256/EdDSA), and includes standard claims: `iss`, `aud`, `sub`, `iat`, `exp`. ([PyJWT][2])

## 2) Validate (verify) tokens

Small class (e.g., `apps/auth/verify_token.py`) using `JwtGuard` or `JwtService`:

```python
from pynest.core import Injectable
from libs.jwt.guard import JwtGuard

@Injectable
class VerifyToken:
    def __init__(self, guard: JwtGuard):
        self.guard = guard

    def run(self, bearer_auth_header: str):
        token = self.guard.token_from_authorization(bearer_auth_header)
        claims = self.guard.verify_access(token)  # validates sig + iss/aud/exp/iat
        return {"sub": claims["sub"], "uname": claims.get("uname")}
```

* Validation enforces **issuer/audience and time claims**; you can also pass leeway (clock skew tolerance) if needed. ([PyJWT][2])

## 3) Renew (refresh) tokens

Single call that checks your **refresh** token and issues a new AT (+ rotates RT by default):

```python
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class RenewTokens:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    def run(self, access_token: str, refresh_token: str):
        return self.jwt.refresh(access_token, refresh_token, rotate_refresh=True)
```

---

# Minimum .env you actually need

Below are **truly minimal** sets for each environment. Keep names as-is; your `ConfService` exposes them as lowercase accessors.

## PROD (asymmetric keys; safest)

Using **RS256** (widely supported). You can swap to ES256/EdDSA later once all verifiers support it. ([PyJWT][3])

```
JWT_ISSUER=THATSEND
JWT_AUDIENCE=Application
JWT_ACCESSTOKEN_EXPIRES_IN=15m
JWT_REFRESHTOKEN_EXPIRES_IN=14d

# Algorithms & key IDs
JWT_SIGNING_ALG_ACCESS=RS256
JWT_SIGNING_ALG_REFRESH=RS256
JWT_KID_ACCESS=v1
JWT_KID_REFRESH=v1

# Key material (PEM files)
JWT_PRIVATE_KEY_ACCESS_PATH=/secrets/jwt_access_private.pem
JWT_PUBLIC_KEY_ACCESS_PATH=/secrets/jwt_access_public.pem
JWT_PRIVATE_KEY_REFRESH_PATH=/secrets/jwt_refresh_private.pem
JWT_PUBLIC_KEY_REFRESH_PATH=/secrets/jwt_refresh_public.pem

# Verification hardening
JWT_LEEWAY=30s
JWT_REQUIRE_EXP=true
JWT_REQUIRE_IAT=true

# (Optional but recommended when other services verify your tokens)
JWT_JWKS_ENABLED=true
JWT_JWKS_CACHE_MAX_AGE=3600
```

Why: RFC 7519 claims + PyJWT verification of `iss`/`aud`/time; asymmetric keys prevent secret sprawl; `kid` supports key rotation; JWKS (RFC 7517) lets other services fetch the public keys. ([IETF Datatracker][4])

## DEV / STAGING (asymmetric or HS\*, your call)

If you already manage dev key files, use the same **PROD** block (best). Otherwise, you can go **HS256** with strong secrets:

```
# Core
JWT_ISSUER=THATSEND
JWT_AUDIENCE=Application
JWT_ACCESSTOKEN_EXPIRES_IN=15m
JWT_REFRESHTOKEN_EXPIRES_IN=14d

# Use HMAC in dev ONLY (simpler bootstrap)
JWT_SIGNING_ALG_ACCESS=HS256
JWT_SIGNING_ALG_REFRESH=HS256
JWT_ACCESSTOKEN_SECRET=dev-acc-secret-32-bytes-minimum________________
JWT_REFRESHTOKEN_SECRET=dev-ref-secret-32-bytes-minimum________________

# Verification
JWT_LEEWAY=30s
JWT_REQUIRE_EXP=true
JWT_REQUIRE_IAT=true
```

HS256 secrets must be **at least the hash size** (≥256 bits for HS256) to avoid brute forcing; OWASP calls this out. ([OWASP Foundation][5])

## LOCAL (fastest bootstrap)

Same as **DEV HS256**—just shorter TTLs so you can test refresh quickly:

```
JWT_ISSUER=THATSEND
JWT_AUDIENCE=Application
JWT_ACCESSTOKEN_EXPIRES_IN=5m
JWT_REFRESHTOKEN_EXPIRES_IN=1d

JWT_SIGNING_ALG_ACCESS=HS256
JWT_SIGNING_ALG_REFRESH=HS256
JWT_ACCESSTOKEN_SECRET=local-acc-secret-32-bytes-minimum________________
JWT_REFRESHTOKEN_SECRET=local-ref-secret-32-bytes-minimum________________

JWT_LEEWAY=30s
JWT_REQUIRE_EXP=true
JWT_REQUIRE_IAT=true
```

---

# Minimal “how-to” toggles (no redeploy)

* **Shorten/extend TTLs at runtime**

  ```python
  jwt_service.configure({"access_expires_in": "10m"})
  ```
* **Switch algorithms (e.g., to ES256)**

  ```python
  jwt_service.configure({"alg_access": "ES256", "alg_refresh": "ES256"})
  ```
* **Rotate keys** (after you place new PEMs)

  ```python
  jwt_service.set_active_key("access", "v2", {"private": new_priv, "public": new_pub})
  jwt_service.configure({"kid_access": "v2"})
  ```

These knobs map to PyJWT’s encode/decode and verification settings (algorithms list, issuer, audience, leeway). ([PyJWT][2])

---

## Why this is “minimum”

* We only set **issuer**, **audience**, **exp**/**iat**, **alg**, and **key/secret**—the bare essentials PyJWT needs to **encode** and **decode** safely with proper validation. ([PyJWT][2])
* Everything else (custom claims like `uname`, `role`, `sess`) is **optional** and passed via `payload_overrides` when you need it—no extra envs required.
* JWKS is optional unless you have external verifiers; it’s the standard way to publish public keys (RFC 7517). ([IETF Datatracker][6])


[1]: https://pyjwt.readthedocs.io/?utm_source=chatgpt.com "Welcome to PyJWT — PyJWT 2.10.1 documentation"
[2]: https://pyjwt.readthedocs.io/en/stable/api.html?utm_source=chatgpt.com "API Reference — PyJWT 2.10.1 documentation - Read the Docs"
[3]: https://pyjwt.readthedocs.io/en/stable/algorithms.html?utm_source=chatgpt.com "Digital Signature Algorithms — PyJWT 2.10.1 documentation"
[4]: https://datatracker.ietf.org/doc/html/rfc7519?utm_source=chatgpt.com "RFC 7519 - JSON Web Token (JWT)"
[5]: https://owasp.org/www-chapter-vancouver/assets/presentations/2020-01_Attacking_and_Securing_JWT.pdf?utm_source=chatgpt.com "Attacking and Securing JWT"
[6]: https://datatracker.ietf.org/doc/html/rfc7517?utm_source=chatgpt.com "RFC 7517 - JSON Web Key (JWK)"

---

for RS256 i have to pass PEM files path can't it be done using JWT_ACCESSTOKEN_SECRET JWT_REFRESHTOKEN_SECRET ? its so tedious work tocreate those or explain the way to generate it to once i do and save those at project folder or any place i just downlaod it and put it in folder

Short answer: **No** — `JWT_ACCESSTOKEN_SECRET` / `JWT_REFRESHTOKEN_SECRET` are for **HS**\* (HMAC) algorithms like HS256. **RS256** is *asymmetric* and **must** use a private key to sign and a *public* key to verify. You can store those keys as files **or** put the PEM text directly in env vars, but they’re still keys (not HMAC secrets). ([PyJWT][1])

Below are the **fastest ways** to get RS256 working, with options so you can pick your pain-free setup.

---

# Option A — Easiest in prod: RS256 with key files (2 min)

1. **Generate keys (once)**

```bash
# make a folder that won't be committed
mkdir -p secrets/jwt && echo "secrets/jwt/*" >> .gitignore

# ACCESS keypair (RSA 2048 is fine; 3072 if you want more margin)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out secrets/jwt/access_private.pem
openssl pkey -in secrets/jwt/access_private.pem -pubout -out secrets/jwt/access_public.pem

# REFRESH keypair
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out secrets/jwt/refresh_private.pem
openssl pkey -in secrets/jwt/refresh_private.pem -pubout -out secrets/jwt/refresh_public.pem

chmod 600 secrets/jwt/*.pem
```

* `genpkey` creates a PKCS#8 private key (PEM by default); `pkey -pubout` derives the public key. ([docs.openssl.org][2])
* RSA 2048/3072 are standard; 2048 is a reasonable default. ([cryptography.io][3])

2. **Point your env at the files**

```
JWT_SIGNING_ALG_ACCESS=RS256
JWT_SIGNING_ALG_REFRESH=RS256
JWT_PRIVATE_KEY_ACCESS_PATH=./secrets/jwt/access_private.pem
JWT_PUBLIC_KEY_ACCESS_PATH=./secrets/jwt/access_public.pem
JWT_PRIVATE_KEY_REFRESH_PATH=./secrets/jwt/refresh_private.pem
JWT_PUBLIC_KEY_REFRESH_PATH=./secrets/jwt/refresh_public.pem
JWT_KID_ACCESS=v1
JWT_KID_REFRESH=v1
```

That’s it — our `JwtService` will sign with the private keys and verify with the public keys. (PyJWT’s RS256 needs real key material, not HMAC secrets.) ([PyJWT][1])

---

# Option B — No files: keep keys **in env vars** (still RS256)

If you don’t want files at all, you can store PEM text directly in envs and load them from config:

* Put the **entire** PEM into envs (newlines allowed if your platform supports multiline envs):

```
JWT_PRIVATE_KEY_ACCESS_PEM="-----BEGIN PRIVATE KEY-----\n...snip...\n-----END PRIVATE KEY-----\n"
JWT_PUBLIC_KEY_ACCESS_PEM="-----BEGIN PUBLIC KEY-----\n...snip...\n-----END PUBLIC KEY-----\n"
# same for refresh
```

* Or base64 the files and store single-line envs:

```bash
base64 -w0 secrets/jwt/access_private.pem > access_private.b64   # macOS: `base64 -i ... -o ...`
# then set JWT_PRIVATE_KEY_ACCESS_B64 to the file contents
```

PyJWT is happy to receive **PEM strings** (not just paths), so this approach is valid — it’s just a different place to store the same keys. If you want, I can add tiny changes so the keystore reads `*_PEM` / `*_B64` envs in addition to the `*_PATH` ones. ([PyJWT][1])

---

# Option C — Stick with secrets only (HS256) for **dev/local**

If your goal is “no keys, no files” during development, set:

```
JWT_SIGNING_ALG_ACCESS=HS256
JWT_SIGNING_ALG_REFRESH=HS256
JWT_ACCESSTOKEN_SECRET=local-acc-secret-32-bytes-minimum________________
JWT_REFRESHTOKEN_SECRET=local-ref-secret-32-bytes-minimum________________
```

Then **switch to RS256 in prod** with the file/env-key options above. (HS\* uses one shared secret; RS\* uses a keypair.) ([PyJWT][4])

---

## Bonus: prefer Ed25519 if you want smaller keys (optional)

If your verifiers support it, **EdDSA (Ed25519)** is compact and easy to generate:

```bash
openssl genpkey -algorithm Ed25519 -out secrets/jwt/access_private.pem
openssl pkey -in secrets/jwt/access_private.pem -pubout -out secrets/jwt/access_public.pem
```

Set `JWT_SIGNING_ALG_ACCESS=EdDSA` (and same for refresh). PyJWT supports EdDSA; it’s standardized in RFC 8037. ([PyJWT][1])

---

## Quick sanity checks

* **Does RS256 need PEM keys?** Yes — a private key to sign, and the public key to verify. HMAC secrets won’t work with RS256. ([PyJWT][1])
* **Can PEM live in envs?** Yes. PyJWT accepts key **strings** (PEM) directly; you don’t have to use files. ([PyJWT][1])
* **Which key sizes?** RSA 2048+ (3072 if you want more margin). ([cryptography.io][3])
* **Where does `kid` help?** We put `kid` in the header so you can rotate keys and publish both in JWKS until the old tokens expire. (JWKS is the standard JSON format for public keys.) ([PyJWT][1])

---

## Minimal “one-and-done” script (copy/paste)

If you just want to generate everything in one go and drop into your repo’s `secrets/jwt` folder:

```bash
mkdir -p secrets/jwt

# ACCESS
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out secrets/jwt/access_private.pem
openssl pkey -in secrets/jwt/access_private.pem -pubout -out secrets/jwt/access_public.pem

# REFRESH
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out secrets/jwt/refresh_private.pem
openssl pkey -in secrets/jwt/refresh_private.pem -pubout -out secrets/jwt/refresh_public.pem

chmod 600 secrets/jwt/*.pem
echo "secrets/jwt/*" >> .gitignore
```

OpenSSL’s `genpkey` / `pkey` are the modern, cross-algo commands. ([docs.openssl.org][2])

---

If you want, I can tweak our keystore to **also** accept `JWT_PRIVATE_KEY_*_PEM` / `*_B64` so you can go entirely fileless in any environment and keep your current DI module unchanged.

[1]: https://pyjwt.readthedocs.io/en/latest/usage.html "Usage Examples — PyJWT 2.10.1 documentation"
[2]: https://docs.openssl.org/3.1/man1/openssl-genpkey/?utm_source=chatgpt.com "openssl-genpkey"
[3]: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/?utm_source=chatgpt.com "RSA — Cryptography 47.0.0.dev1 documentation"
[4]: https://pyjwt.readthedocs.io/en/stable/algorithms.html?utm_source=chatgpt.com "Digital Signature Algorithms — PyJWT 2.10.1 documentation"

---

give me use case to validate Graphql request Token will be sent as Auth barier token how to use in code, what to input and what output will be proided graphql service will use this as DI

---

awesome — here’s a clean, PyNest-style “use case” for **validating GraphQL requests with a Bearer token**, using **JwtGuard/JwtService via DI**. You’ll plug this into Strawberry’s `context_getter` so every resolver gets a trusted `context.user/claims`. (Strawberry recommends auth at the framework/context layer; `context_getter` is the canonical hook.) ([strawberry.rocks][1])

---

# What the client sends (input)

* HTTP header on the GraphQL POST (or WS handshake):

  ```
  Authorization: Bearer <JWT>
  ```

  This is the standard pattern; the server pulls the token from `Authorization` and attaches the user to the GraphQL **context** for resolvers to use. ([apollographql.com][2])

---

# What your resolvers receive (output)

After validation, your resolvers can read from `info.context`:

```json
{
  "is_authenticated": true,
  "user": { "id": "u_123", "uname": "core", "role": "admin" },
  "claims": { "sub": "u_123", "uname": "core", "scopes": ["user.read"], "au": 9, "iat": 169..., "exp": 169... },
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

On failure (missing/invalid/expired token), resolvers see:

```json
{ "is_authenticated": false, "user": null, "claims": null, "token": null }
```

(You can also throw a GraphQL error with `extensions.code = "UNAUTHENTICATED"` in your resolver if you *require* auth.) Authorization is usually enforced in resolvers/services (e.g., scope/tenant checks). ([GraphQL][3])

---

# Drop-in DI classes (1 class/file, no code outside classes)

These examples assume you already registered `JwtModule` so `JwtGuard`/`JwtService` are injectable.

## 1) Build the GraphQL context from the Bearer token

Use Strawberry’s `context_getter` hook (FastAPI or equivalent integration) to call this DI class and attach `user/claims`. ([strawberry.rocks][1])

```python
# libs/graphql/auth_context_builder.py
from pynest.core import Injectable
from libs.jwt.guard import JwtGuard

@Injectable
class GraphQLAuthContextBuilder:
    def __init__(self, guard: JwtGuard, log):
        self.guard = guard
        self.log = log

    async def build(self, request):
        # 1) Extract "Authorization: Bearer <token>"
        token = self.guard.token_from_authorization(request.headers.get("Authorization"))
        if not token:
            return {"request": request, "is_authenticated": False, "user": None, "claims": None, "token": None}

        # 2) Verify signature + iss/aud/exp/iat using JwtService under the hood
        #    (PyJWT enforces these when passed via decode options)
        #    -> success: claims dict; failure: raises InvalidTokenError. :contentReference[oaicite:4]{index=4}
        try:
            claims = self.guard.verify_access(token)
        except Exception as ex:
            self.log.warn("GraphQL auth failed: %s", ex)
            return {"request": request, "is_authenticated": False, "user": None, "claims": None, "token": None}

        # 3) Shape a compact user snapshot for resolvers
        user = {
            "id": claims.get("sub"),
            "uname": claims.get("uname"),
            "role": claims.get("role"),
            "au": claims.get("au"),
            "scopes": claims.get("scopes", []),
        }
        return {"request": request, "is_authenticated": True, "user": user, "claims": claims, "token": token}
```

> Why this is the recommended spot: Strawberry’s docs show that `context_getter` is designed to inject per-request data (like auth) into resolvers. ([strawberry.rocks][1])

## 2) Plug the builder into your GraphQL service

Your GraphQL “service” (the thing that creates the Strawberry router/app) takes the builder and passes its `build` method to Strawberry’s `context_getter`. ([strawberry.rocks][1])

```python
# libs/graphql/graphql_service.py
from pynest.core import Injectable
from strawberry.fastapi import GraphQLRouter  # or integration you're using
# from strawberry.schema import Schema  # import your built schema

from libs.graphql.auth_context_builder import GraphQLAuthContextBuilder

@Injectable
class GraphQLService:
    def __init__(self, ctx: GraphQLAuthContextBuilder, schema, conf, log):
        self.ctx = ctx
        self.schema = schema
        self.conf = conf
        self.log = log

    def build_router(self):
        # Strawberry + FastAPI example; similar for other integrations
        return GraphQLRouter(
            schema=self.schema,
            context_getter=self.ctx.build,  # <= DI-powered context
            # you can also pass dependencies=[], graphiql=..., etc.
        )
```

> In Strawberry, the context is then available to every resolver via `info.context`. The “Intro to Strawberry” tutorial also demonstrates context usage. ([apollographql.com][4])

## 3) Simple resolver/service check examples

Use the data we put into context; do NOT parse headers inside resolvers.

```python
# apps/users/user_read_service.py
from pynest.core import Injectable

@Injectable
class UserReadService:
    def __init__(self, repo):
        self.repo = repo

    async def list_for_tenant(self, au: int):
        return await self.repo.list_for_tenant(au)
```

```python
# apps/users/user_resolver_guard.py
from pynest.core import Injectable, ForbiddenException

@Injectable
class UserResolverGuard:
    def require_scopes(self, ctx, needed):
        scopes = set((ctx.get("user") or {}).get("scopes", []))
        if not set(needed).issubset(scopes):
            raise ForbiddenException("missing required scope(s)")

    def require_tenant(self, ctx, au):
        if str((ctx.get("user") or {}).get("au")) != str(au):
            raise ForbiddenException("tenant mismatch")
```

```python
# apps/users/user_resolver.py
from pynest.core import Injectable
from .user_read_service import UserReadService
from .user_resolver_guard import UserResolverGuard

@Injectable
class UserResolver:
    def __init__(self, svc: UserReadService, guard: UserResolverGuard):
        self.svc = svc
        self.guard = guard

    async def users(self, info, au: int):
        ctx = info.context
        if not ctx.get("is_authenticated"):
            # let GraphQL client see a clear “unauthenticated” error if you prefer raising here
            raise Exception("UNAUTHENTICATED")

        self.guard.require_scopes(ctx, ["user.read"])
        self.guard.require_tenant(ctx, au)

        return await self.svc.list_for_tenant(au)
```

* Strawberry’s permissions guide also shows reading the `Authorization` header from `info.context["request"]` if you prefer DIY in a permission class, but putting the logic in `context_getter` keeps resolvers clean. ([strawberry.rocks][5])

---

## End-to-end behavior (happy path and failures)

**Happy path (valid Bearer token):**

1. Client sends `Authorization: Bearer <JWT>`.
2. `GraphQLAuthContextBuilder.build()` extracts & verifies with `JwtGuard` → PyJWT checks signature + `iss/aud/exp/iat` (with your leeway). ([PyJWT][6])
3. `context` gets `{ is_authenticated: true, user, claims }`.
4. Resolver reads `info.context.user` and passes scope/tenant checks, returns data.

**Failure:**

* Missing header → `is_authenticated: false` in context; resolver can return public data or raise `UNAUTHENTICATED`.
* Bad/expired token → verify raises; context marks unauthenticated (or you can short-circuit with a GraphQL error). (PyJWT exposes `InvalidTokenError` and validates time claims; you can configure `leeway`.) ([PyJWT][6])

---

## Quick checklist you can hand to the team

* **Client:** send `Authorization: Bearer <JWT>` with every GraphQL request. ([apollographql.com][2])
* **Server wiring:** pass DI-built `context_getter` to Strawberry so resolvers get `context.user/claims`. ([strawberry.rocks][1])
* **Validation:** `JwtGuard.verify_access()` (under the hood PyJWT `decode`) enforces signature + `iss/aud/exp/iat`; adjust `leeway` in your env if needed. ([PyJWT][6])
* **Authorization:** check scopes/tenant in resolvers/services using the values from `context`. (GraphQL separates authentication from authorization.) ([GraphQL][3])

If you want, I can tailor these snippets to your exact **StrawberryGraphQLService** builder (the one you mentioned earlier), so you can paste in the DI wiring and be live in minutes.

[1]: https://strawberry.rocks/docs/integrations/fastapi?utm_source=chatgpt.com "FastAPI | 🍓 Strawberry GraphQL"
[2]: https://www.apollographql.com/docs/react/networking/authentication?utm_source=chatgpt.com "Authentication - Apollo GraphQL Docs"
[3]: https://graphql.org/learn/authorization/?utm_source=chatgpt.com "Authorization"
[4]: https://www.apollographql.com/tutorials/intro-strawberry/09-the-context?utm_source=chatgpt.com "The context - GraphQL Tutorials"
[5]: https://strawberry.rocks/docs/guides/permissions?utm_source=chatgpt.com "Permissions"
[6]: https://pyjwt.readthedocs.io/en/stable/api.html?utm_source=chatgpt.com "API Reference — PyJWT 2.10.1 documentation - Read the Docs"


---

below are **practical, copy-paste example files** that show how to use both **JwtService** and **JwtGuard** across common app surfaces (REST, GraphQL, CLI, jobs, websockets, admin, tests). Each example keeps your PyNest rules: **1 class per file, no code outside classes, no nesting**, DI everywhere.

These follow PyNest’s module/provider DI pattern and PyJWT’s verified usage for `encode/decode`, `aud/iss`, and `leeway`. ([Python Nest][1])

---

## 1) Login / issue tokens (Service uses `JwtService`)

```python
# apps/auth/auth_service.py
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class AuthService:
    def __init__(self, jwt: JwtService, user_repo, conf, log):
        self.jwt = jwt
        self.user_repo = user_repo
        self.conf = conf
        self.log = log

    async def login(self, uname: str, password: str) -> dict:
        user = await self.user_repo.verify(uname, password)
        # sub is your unique id; carry extras on demand
        access = self.jwt.sign_access(
            sub=user.id,
            scopes=["user.read", "user.write"],
            au=user.au,
            payload_overrides={
                "uname": user.uname,
                "email": user.email,
                "role": user.role,
                "sess": {"id": user.session_id},
                "udvc": {"device_id": user.device_id},
            },
        )
        refresh = self.jwt.sign_refresh(
            sub=user.id,
            au=user.au,
            payload_overrides={"sess": {"id": user.session_id}},
        )
        return {"access": access, "refresh": refresh}
```

---

## 2) REST controller using `JwtGuard` (header or cookie)

```python
# apps/auth/auth_controller.py
from pynest.core import Controller, Post
from libs.jwt.guard import JwtGuard
from .auth_service import AuthService

@Controller("/auth")
class AuthController:
    def __init__(self, svc: AuthService, guard: JwtGuard):
        self.svc = svc
        self.guard = guard

    @Post("/login")
    async def login(self, body):
        # body contains uname/password; keep example short
        tokens = await self.svc.login(body["uname"], body["password"])
        return {"access": tokens["access"], "refresh": tokens["refresh"]}

    @Post("/me")
    async def me(self, request):
        token = self.guard.token_from_authorization(request.headers.get("Authorization")) \
            or self.guard.token_from_cookies(request.cookies, "at")
        claims = self.guard.verify_access(token)
        return {"sub": claims["sub"], "uname": claims.get("uname"), "scopes": claims.get("scopes", [])}
```

---

## 3) Protected route with scopes + tenant checks

```python
# apps/users/user_controller.py
from pynest.core import Controller, Get, ForbiddenException
from libs.jwt.guard import JwtGuard

@Controller("/users")
class UserController:
    def __init__(self, guard: JwtGuard, user_repo):
        self.guard = guard
        self.user_repo = user_repo

    @Get("/")
    async def list_users(self, request):
        token = self.guard.token_from_authorization(request.headers.get("Authorization"))
        claims = self.guard.verify_access(token)

        if not self.guard.require_scopes(claims, ["user.read"]):
            raise ForbiddenException("Missing scope: user.read")

        # Optional tenant gate
        au = request.query.get("au")
        if au and not self.guard.require_tenant(claims, au):
            raise ForbiddenException("Tenant mismatch")

        return await self.user_repo.list_for_tenant(au or claims.get("au"))
```

---

## 4) Refresh endpoint (rotate by default)

```python
# apps/auth/refresh_controller.py
from pynest.core import Controller, Post
from libs.jwt.service import JwtService
from libs.jwt.guard import JwtGuard

@Controller("/auth")
class RefreshController:
    def __init__(self, jwt: JwtService, guard: JwtGuard):
        self.jwt = jwt
        self.guard = guard

    @Post("/refresh")
    async def refresh(self, request):
        at = self.guard.token_from_authorization(request.headers.get("Authorization"))  # may be expired
        rt = self.guard.token_from_cookies(request.cookies, "rt") or request.body.get("refresh")
        result = self.jwt.refresh(at or "", rt, rotate_refresh=True)
        return result
```

---

## 5) Logout + revoke (denylist a JTI)

```python
# apps/auth/logout_controller.py
from pynest.core import Controller, Post, BadRequestException
from libs.jwt.service import JwtService

@Controller("/auth")
class LogoutController:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    @Post("/logout")
    async def logout(self, body):
        jti = body.get("jti")
        if not jti:
            raise BadRequestException("jti required")
        self.jwt.revoke(jti)
        return {"ok": True}
```

---

## 6) JWKS endpoint (public keys for verifiers)

```python
# apps/jwks/jwks_controller.py
from pynest.core import Controller, Get
from libs.jwt.service import JwtService

@Controller("/.well-known")
class JwksController:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    @Get("/jwks.json")
    async def jwks(self, response):
        data = self.jwt.jwks()  # RFC 7517 JWKS
        # set cache header if you like
        response.headers["Cache-Control"] = f"public, max-age={data.get('cache_max_age', 3600)}"
        return data
```

JWKS format is defined in RFC 7517; exposing public verification keys enables safe `kid` rotation. ([IETF Datatracker][2])

---

## 7) Admin key rotation (hot-swap)

```python
# apps/admin/key_rotation_service.py
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class KeyRotationService:
    def __init__(self, jwt: JwtService, secret_store):
        self.jwt = jwt
        self.secrets = secret_store

    def rotate_access_to_v2(self):
        new = self.secrets.read_keypair("jwt_access_v2")  # returns dict with private/public/secret bytes
        self.jwt.set_active_key("access", "v2", new)      # future tokens use kid=v2

    def rotate_refresh_to_v2(self):
        new = self.secrets.read_keypair("jwt_refresh_v2")
        self.jwt.set_active_key("refresh", "v2", new)
```

---

## 8) CLI mint/verify (handy for support)

```python
# apps/cli/token_cli.py
from pynest.core import CliController, CliCommand
from libs.jwt.service import JwtService

@CliController("token")
class TokenCli:
    def __init__(self, jwt: JwtService, console):
        self.jwt = jwt
        self.console = console

    @CliCommand("mint")
    def mint(self, uname: str, sub: str):
        at = self.jwt.sign_access(sub=sub, payload_overrides={"uname": uname})
        self.console.print(at)

    @CliCommand("verify")
    def verify(self, token: str):
        claims = self.jwt.verify(token, expected_use="access")
        self.console.print(claims)
```

---

## 9) Background worker: batch verify

```python
# apps/jobs/batch_verifier.py
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class BatchVerifierJob:
    def __init__(self, jwt: JwtService, inbox, outbox, log):
        self.jwt = jwt
        self.inbox = inbox
        self.outbox = outbox
        self.log = log

    async def run_once(self):
        events = await self.inbox.pull()
        verified = []
        for e in events:
            try:
                c = self.jwt.verify(e["token"], expected_use="access")
                verified.append({"id": e["id"], "sub": c["sub"]})
            except Exception as ex:
                self.log.warn("verify failed for %s: %s", e["id"], ex)
        await self.outbox.push(verified)
```

---

## 10) GraphQL: put user in context

```python
# apps/graphql/context_auth.py
from pynest.core import Injectable
from libs.jwt.guard import JwtGuard

@Injectable
class GraphQLContextAuth:
    def __init__(self, guard: JwtGuard):
        self.guard = guard

    async def build_context(self, request):
        token = self.guard.token_from_authorization(request.headers.get("Authorization"))
        user = None
        if token:
            try:
                claims = self.guard.verify_access(token)
                user = {"id": claims["sub"], "scopes": claims.get("scopes", [])}
            except Exception:
                user = None
        return {"user": user}
```

---

## 11) WebSocket handshake auth

```python
# apps/ws/ws_auth.py
from pynest.core import Injectable, ForbiddenException
from libs.jwt.guard import JwtGuard

@Injectable
class WebSocketAuth:
    def __init__(self, guard: JwtGuard):
        self.guard = guard

    def authorize(self, headers, query):
        token = self.guard.token_from_authorization(headers.get("Authorization")) or query.get("token")
        if not token:
            raise ForbiddenException("missing token")
        claims = self.guard.verify_access(token)
        if not self.guard.require_scopes(claims, ["ws.connect"]):
            raise ForbiddenException("scope ws.connect required")
        return {"user_id": claims["sub"]}
```

---

## 12) Multi-audience verify (service usage)

```python
# apps/examples/audience_override_service.py
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class AudienceOverrideService:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    def verify_for_two_auds(self, token: str):
        # PyJWT supports iterable 'audience' values for decode. :contentReference[oaicite:2]{index=2}
        return self.jwt.verify(token, expected_use="access", aud=["Application", "AdminPortal"])
```

---

## 13) Custom payload on demand (service usage)

```python
# apps/examples/custom_payload_service.py
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class CustomPayloadService:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    def issue_for_impersonation(self, actor_id: str, target_user):
        return self.jwt.sign_access(
            sub=target_user.id,
            payload_overrides={
                "type": "impersonation",
                "uname": target_user.uname,
                "au": {"impersonated_by": actor_id},
            },
            expires_in="10m",
        )
```

---

## 14) Introspection (pick key by `kid` before verify)

```python
# apps/examples/introspect_then_verify.py
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class IntrospectThenVerify:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    def check(self, token: str):
        meta = self.jwt.introspect(token)  # header/payload w/o signature (routing only) :contentReference[oaicite:3]{index=3}
        # you could decide audience/issuer overrides or pick a tenant-specific key set here
        return self.jwt.verify(token, expected_use="access")
```

---

## 15) Short-lived access for downloads (cookie flow)

```python
# apps/downloads/download_controller.py
from pynest.core import Controller, Get, ForbiddenException
from libs.jwt.guard import JwtGuard

@Controller("/downloads")
class DownloadController:
    def __init__(self, guard: JwtGuard, storage):
        self.guard = guard
        self.storage = storage

    @Get("/file")
    async def file(self, request):
        token = self.guard.token_from_cookies(request.cookies, "at")
        claims = self.guard.verify_access(token)
        if not self.guard.require_scopes(claims, ["download.read"]):
            raise ForbiddenException("missing download.read")
        return await self.storage.get(request.query["id"])
```

---

## 16) Admin: switch algorithms (service config)

```python
# apps/admin/alg_switch_service.py
from pynest.core import Injectable
from libs.jwt.service import JwtService

@Injectable
class AlgSwitchService:
    def __init__(self, jwt: JwtService):
        self.jwt = jwt

    def move_to_es256(self):
        # pin algorithm per OWASP guidance to prevent alg confusion. :contentReference[oaicite:4]{index=4}
        self.jwt.configure({"alg_access": "ES256", "alg_refresh": "ES256"})
```

---

## 17) Tests (class wrapper, no module-level code)

```python
# tests/test_jwt_service_examples.py
import pytest
from libs.jwt.service import JwtService

class JwtServiceExamplesSpec:
    def setup_method(self):
        # DI-less quick wiring for tests: assume HS256 secrets set in test conf
        class DummyConf:
            jwt_issuer = "THATSEND"
            jwt_audience = "Application"
            jwt_accesstoken_expires_in = "5m"
            jwt_refreshtoken_expires_in = "1d"
            jwt_signing_alg_access = "HS256"
            jwt_signing_alg_refresh = "HS256"
            jwt_accesstoken_secret = "secret-acc-256-bits___________"
            jwt_refreshtoken_secret = "secret-ref-256-bits___________"
        self.svc = JwtService(DummyConf(), utils=None, keystore=None, revocation=None)  # your test DI may wrap this

    def test_sign_and_verify(self):
        at = self.svc.sign_access(sub="u1", payload_overrides={"uname": "core"})
        claims = self.svc.verify(at, expected_use="access")
        assert claims["sub"] == "u1"
        assert claims["uname"] == "core"
```

> PyJWT `decode` options validate `aud`/`iss` and support `leeway`; multiple audiences can be supplied. Use `get_unverified_header` for header-only reads (e.g., `kid`). ([PyJWT][3])

---

### Tips you might reference while wiring

* **PyNest DI & modular pattern**: providers registered in a module, exported, and injected by type in controllers/services. ([Python Nest][1])
* **PyJWT**: `jwt.encode(payload, key, algorithm=...)`, `jwt.decode(..., algorithms=[...], audience=..., issuer=..., leeway=...)`. ([PyJWT][4])
* **JWKS**: publish public keys (RSA/EC/OKP) per RFC 7517; include `kid` to enable rotation. ([IETF Datatracker][2])
* **Security**: allow only pinned algorithms; reject `none`; validate `aud/iss`; ensure adequate key sizes. ([OWASP Foundation][5])

---

If you want, I can add **FastAPI cookie examples** (HttpOnly/SameSite) and a **Redis-backed revocation store** in the same “1 class per file” style.

[1]: https://pythonnest.github.io/PyNest/introduction/?utm_source=chatgpt.com "Introduction - PyNest"
[2]: https://datatracker.ietf.org/doc/html/rfc7517?utm_source=chatgpt.com "RFC 7517 - JSON Web Key (JWK)"
[3]: https://pyjwt.readthedocs.io/en/stable/api.html?utm_source=chatgpt.com "API Reference — PyJWT 2.10.1 documentation - Read the Docs"
[4]: https://pyjwt.readthedocs.io/en/stable/usage.html?utm_source=chatgpt.com "Usage Examples — PyJWT 2.10.1 documentation"
[5]: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/06-Session_Management_Testing/10-Testing_JSON_Web_Tokens?utm_source=chatgpt.com "OWASP - Testing JSON Web Tokens"

great question — here’s a tight, single-source guide to **every configurable knob** in your JWT module and **exactly how to set each one** (env → Conf → runtime → per-call). I’ve grounded the behaviors in PyJWT docs, the JWT/JWK RFCs, and OWASP best practices. ([PyJWT][1])

---

# 1) Configure via `.env` → `ConfService` (global defaults)

These become lowercase accessors on `conf.*` (per your convention).

| ENV variable                   | Conf accessor                       | Purpose                                                         | Type / allowed                                                         | Default                                      |
| ------------------------------ | ----------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------- |
| `JWT_ISSUER`                   | `conf.jwt_issuer`                   | Sets `iss` for all tokens; verified on decode.                  | string                                                                 | `THATSEND`                                   |
| `JWT_AUDIENCE`                 | `conf.jwt_audience`                 | Sets `aud`; accept string or list. PyJWT can validate audience. | string or JSON list                                                    | `Application` ([PyJWT][2])                   |
| `JWT_ACCESSTOKEN_EXPIRES_IN`   | `conf.jwt_accesstoken_expires_in`   | Access token TTL.                                               | `30s`, `15m`, `1h`, `1d`, etc.                                         | `15m`                                        |
| `JWT_REFRESHTOKEN_EXPIRES_IN`  | `conf.jwt_refreshtoken_expires_in`  | Refresh token TTL.                                              | same formats                                                           | `14d`                                        |
| `JWT_SIGNING_ALG_ACCESS`       | `conf.jwt_signing_alg_access`       | Algorithm for access tokens.                                    | `RS256`, `RS512`, `PS256`, `ES256`, `EdDSA`, (`HS256`,`HS512` for dev) | `RS256` ([PyJWT][3])                         |
| `JWT_SIGNING_ALG_REFRESH`      | `conf.jwt_signing_alg_refresh`      | Algorithm for refresh tokens.                                   | same as above                                                          | `RS256`                                      |
| `JWT_PRIVATE_KEY_ACCESS_PATH`  | `conf.jwt_private_key_access_path`  | Private key PEM path (RSA/ECDSA/Ed25519).                       | file path                                                              | —                                            |
| `JWT_PUBLIC_KEY_ACCESS_PATH`   | `conf.jwt_public_key_access_path`   | Public key PEM path for verification/JWKS.                      | file path                                                              | —                                            |
| `JWT_PRIVATE_KEY_REFRESH_PATH` | `conf.jwt_private_key_refresh_path` | Private key PEM for refresh.                                    | file path                                                              | —                                            |
| `JWT_PUBLIC_KEY_REFRESH_PATH`  | `conf.jwt_public_key_refresh_path`  | Public key PEM for refresh.                                     | file path                                                              | —                                            |
| `JWT_ACCESSTOKEN_SECRET`       | `conf.jwt_accesstoken_secret`       | **Dev only** HMAC secret if using HS\*.                         | ≥256-bit string                                                        | — (use keys in prod) ([OWASP Foundation][4]) |
| `JWT_REFRESHTOKEN_SECRET`      | `conf.jwt_refreshtoken_secret`      | **Dev only** HMAC secret for refresh.                           | ≥256-bit string                                                        | —                                            |
| `JWT_KID_ACCESS`               | `conf.jwt_kid_access`               | Current key id for access (goes in JWT header).                 | string                                                                 | `v1`                                         |
| `JWT_KID_REFRESH`              | `conf.jwt_kid_refresh`              | Current key id for refresh.                                     | string                                                                 | `v1`                                         |
| `JWT_LEEWAY`                   | `conf.jwt_leeway`                   | Allowed clock skew during verify.                               | seconds or duration                                                    | `30s` ([PyJWT][5])                           |
| `JWT_REQUIRE_EXP`              | `conf.jwt_require_exp`              | Require `exp` claim.                                            | `true`/`false`                                                         | `true` ([PyJWT][6])                          |
| `JWT_REQUIRE_IAT`              | `conf.jwt_require_iat`              | Require `iat` claim.                                            | `true`/`false`                                                         | `true` ([PyJWT][6])                          |
| `JWT_JWKS_ENABLED`             | `conf.jwt_jwks_enabled`             | Expose public keys via JWKS.                                    | `true`/`false`                                                         | `false`                                      |
| `JWT_JWKS_CACHE_MAX_AGE`       | `conf.jwt_jwks_cache_max_age`       | Cache‐control (seconds) for JWKS.                               | int                                                                    | `3600`                                       |

**Why these matter:** Issuer/audience and claim checks (`exp/iat/nbf`) are first-class in PyJWT, and leeway is supported to handle small clock skews. Algorithm choices include RSA/ECDSA and modern **EdDSA** (Ed25519) with `cryptography` installed; JWKS follows RFC 7517 for sharing public keys with a `kid` for rotation. ([PyJWT][2])

---

# 2) Configure at runtime (service-level) with `JwtService.configure(...)`

Use this to change behavior **without redeploying** (e.g., A/B switching algorithms, tightening TTLs):

* `issuer` → overrides global `iss`
* `audience` → string or list override
* `access_expires_in`, `refresh_expires_in` → duration strings (e.g., `"10m"`, `"30d"`)
* `leeway` → `"45s"` etc. (PyJWT accepts seconds or `timedelta` for leeway) ([PyJWT][5])
* `alg_access`, `alg_refresh` → pin per-type algorithms (prevents alg-confusion risks; recommended by OWASP). ([OWASP Foundation][4])
* `kid_access`, `kid_refresh` → flip active key ids during rotation.

> Pinning permitted algorithms and validating `iss`/`aud` are standard hardening steps. ([OWASP Foundation][4])

---

# 3) Configure per call (minting) — **fine-grained control**

Both `sign_access(...)` and `sign_refresh(...)` accept:

* `sub` *(required)* → your unique id.
* `aud` → override audience for this token only (string or list per spec). ([PyJWT][2])
* `au` → becomes `au` when present.
* `scopes` → array of scopes (optional).
* `payload_overrides` → **safe custom additions** like `uname`, `email`, `role`, `au`, `udvc`, `sess`. The service blocks reserved claims (`iss`, `aud`, `exp`, `iat`, `nbf`, `jti`, `typ`).
* `expires_in` → override TTL just for this token (e.g., short-lived download tokens).
* `kid`, `algorithm` → force a specific key/alg for this mint (rare; usually keep defaults).
* `additional_headers` → add extra JWS header fields if needed (e.g., custom `cty`).

---

# 4) Configure verification (guard/service)

* `verify(token, expected_use="access"|"refresh", aud=None, iss=None, leeway=None)`

  * You can **tighten** the expected `aud/iss` at call-site.
  * Leeway can be overridden per verification if a boundary needs extra skew.
  * PyJWT enforces the registered claims and supports leeway and multiple audiences. ([PyJWT][6])

* **Extraction strategy** (in `JwtGuard`): you decide where tokens come from.

  * `Authorization: Bearer <token>` (default)
  * Cookies: you choose cookie names (`at`, `rt`, etc.) when reading via `token_from_cookies(cookies, name)`
  * Query (WS) as a fallback during handshake.
    *(Cookie names/domains aren’t hardcoded — you can standardize them via your own envs if you want.)*

* **Policy checks**:

  * `require_scopes(claims, ["feature.read"])`
  * `require_tenant(claims, au)`

---

# 5) Key & algorithm posture (what/why/how to set)

* **Recommended for prod**: `RS256` (widely supported) or `ES256` (smaller/faster) or **`EdDSA`** (Ed25519) if all verifiers support it. PyJWT documents EdDSA and ECDSA support (requires `cryptography`). ([PyJWT][3])
* **Dev only**: `HS256/HS512` with strong secrets. Ensure key size ≥ hash size; weak HMAC secrets are risky. ([OWASP Foundation][4])
* **Rotation**: set new `JWT_KID_*` and key paths, then flip via `JwtService.set_active_key(...)`. Publish both keys in JWKS until old tokens age out (JWKS per RFC 7517). ([IETF Datatracker][7])

---

# 6) JWKS exposure (optional but recommended with asymmetric)

* Enable with `JWT_JWKS_ENABLED=true` and mount a tiny controller that returns `jwt_service.jwks()` at `/.well-known/jwks.json`.
* JWKS properties (`kty`, `alg`, `kid`, etc.) come from RFC 7517 / JWA registries; clients cache per `JWT_JWKS_CACHE_MAX_AGE`. ([IETF Datatracker][7])

---

# 7) Revocation / rotation behavior (operational knobs)

* **Denylist**: `jwt_service.revoke(jti, until=...)` and `is_revoked(jti)` — in-memory by default; you can swap the store provider for Redis/Postgres without touching callers.
* **Refresh rotation**: `jwt_service.refresh(at, rt, rotate_refresh=True)` (default) revokes old RT’s `jti` and returns a new RT + AT.
* **Reuse detection hook**: the method exposes a callback parameter so you can act on suspected token theft in your implementation.

---

# 8) Minimal “how do I set it” playbook

**A. `.env` for prod (RSA/ES/EdDSA)**

```
JWT_ISSUER=THATSEND
JWT_AUDIENCE=Application
JWT_ACCESSTOKEN_EXPIRES_IN=15m
JWT_REFRESHTOKEN_EXPIRES_IN=14d
JWT_SIGNING_ALG_ACCESS=RS256
JWT_SIGNING_ALG_REFRESH=RS256
JWT_PRIVATE_KEY_ACCESS_PATH=/secrets/jwt_access.pem
JWT_PUBLIC_KEY_ACCESS_PATH=/secrets/jwt_access.pub
JWT_PRIVATE_KEY_REFRESH_PATH=/secrets/jwt_refresh.pem
JWT_PUBLIC_KEY_REFRESH_PATH=/secrets/jwt_refresh.pub
JWT_KID_ACCESS=v1
JWT_KID_REFRESH=v1
JWT_LEEWAY=30s
JWT_REQUIRE_EXP=true
JWT_REQUIRE_IAT=true
JWT_JWKS_ENABLED=true
JWT_JWKS_CACHE_MAX_AGE=3600
```

**B. Flip something at runtime (no redeploy)**

```python
jwt_service.configure({
  "access_expires_in": "10m",
  "alg_access": "ES256",    # when all verifiers support it
  "kid_access": "v2"        # after loading new keys
})
```

(Leeway, audience, issuer, and allowed algorithms are all supported by the PyJWT verify options. ([PyJWT][6]))

**C. Per-call custom claim**

```python
jwt_service.sign_access(
  sub=user_id,
  payload_overrides={"uname": "core", "role": "admin", "sess": {"id": "S123"}}
)
```

Registered claims stay service-owned; extras like `uname`, `role`, `sess` are allowed. (Registered claims list: `exp/nbf/iss/aud/iat` etc.) ([PyJWT][2])

---

# 9) Quick reference — what each knob influences

* **Issuer / Audience** → signature **and** validation gate; tokens are rejected when `aud/iss` don’t match. ([PyJWT][2])
* **Leeway** → tolerance around `exp/iat/nbf`. Seconds or `timedelta`. ([PyJWT][5])
* **Algorithms** → signature method; pinning avoids alg-confusion attacks; EdDSA/ECDSA require `cryptography`. ([OWASP Foundation][4])
* **KID** → selects the right verification key; surfaced in header and JWKS for clients. ([IETF Datatracker][7])
* **TTLs** → token validity windows; keep **access** short and **refresh** longer (with rotation).

---

# 10) Sanity presets

* **Local/dev**: HS256/HS512 + strong secrets (`JWT_*SECRET`), short TTLs, `JWT_JWKS_ENABLED=false`.
* **Staging/Prod**: RS256/ES256/**EdDSA**, JWKS enabled, rotation via `kid`, strict `iss/aud`, small `leeway` (≤30s). (EdDSA/Ed25519 is defined for JOSE in RFC 8037; PyJWT supports it.) ([RFC Editor][8])

---

## TL;DR

* **Global**: set envs → `ConfService` (issuer, audience, TTLs, alg, keys, kid, leeway, JWKS).
* **Runtime**: `jwt_service.configure()` to flip alg/ttl/kid/audience/issuer/leeway.
* **Per-call**: `payload_overrides`, per-token TTL, audience, etc.
* **Verify**: tighten `aud/iss/leeway` per request; guard handles extraction & basic policy checks.
* **Keys**: rotate via `kid` + JWKS; keep old public key published until tokens expire. ([IETF Datatracker][7])

If you want, I can bundle these into a one-page “JWT Config README” for your repo, plus a tiny JWKS controller and (optional) Redis revocation provider—all still in your **1-class-per-file** PyNest style.

[1]: https://pyjwt.readthedocs.io/?utm_source=chatgpt.com "Welcome to PyJWT — PyJWT 2.10.1 documentation"
[2]: https://pyjwt.readthedocs.io/en/stable/usage.html?utm_source=chatgpt.com "Usage Examples — PyJWT 2.10.1 documentation"
[3]: https://pyjwt.readthedocs.io/en/stable/algorithms.html?utm_source=chatgpt.com "Digital Signature Algorithms — PyJWT 2.10.1 documentation"
[4]: https://owasp.org/www-chapter-vancouver/assets/presentations/2020-01_Attacking_and_Securing_JWT.pdf?utm_source=chatgpt.com "Attacking and Securing JWT"
[5]: https://pyjwt.readthedocs.io/en/latest/usage.html?utm_source=chatgpt.com "Usage Examples — PyJWT 2.10.1 documentation - Read the Docs"
[6]: https://pyjwt.readthedocs.io/en/stable/api.html?utm_source=chatgpt.com "API Reference — PyJWT 2.10.1 documentation - Read the Docs"
[7]: https://datatracker.ietf.org/doc/html/rfc7517?utm_source=chatgpt.com "RFC 7517 - JSON Web Key (JWK)"
[8]: https://www.rfc-editor.org/info/rfc8037?utm_source=chatgpt.com "Information on RFC 8037"

great call. here’s a clear, “what stays / what changes” guide for your **old JWT env vars**—what each one does now, how the module uses it, and any caveats or best-practice notes.

---

# Old envs → how they’re used today

## 1) `JWT_ISSUER` → `conf.jwt_issuer`

* **What it does:** Sets the `iss` claim on every token and is **validated** during `verify(...)`.
* **Scope:** Global default; can be overridden per-verify call (`verify(..., iss="...")`) or at runtime via `jwt_service.configure({"issuer": "..."})`.
* **Why it matters:** `iss` is a registered JWT claim; validating it is recommended. ([IETF Datatracker][1])

## 2) `JWT_AUDIENCE` → `conf.jwt_audience`

* **What it does:** Sets the `aud` claim on minted tokens and is **validated** on `verify(...)`.
* **Accepted forms:** String (single audience) or list/array (multiple audiences). PyJWT supports passing an iterable for `audience` during decode. ([PyJWT][2])
* **Override points:** Per-call on sign (`sign_access(..., aud=...)`) and per-verify (`verify(..., aud=...)`).

## 3) `JWT_ACCESSTOKEN_EXPIRES_IN` → `conf.jwt_accesstoken_expires_in`

* **What it does:** Default **TTL** for access tokens (e.g., `15m`). Parsed by our duration helper (supports `30s`, `15m`, `1h`, `1d`, or integer seconds).
* **Override points:** Per-call via `sign_access(..., expires_in="10m")` or at runtime with `jwt_service.configure({"access_expires_in":"10m"})`.

## 4) `JWT_REFRESHTOKEN_EXPIRES_IN` → `conf.jwt_refreshtoken_expires_in`

* **What it does:** Default **TTL** for refresh tokens (e.g., `14d`).
* **Override points:** Per-call via `sign_refresh(..., expires_in="30d")` or runtime via `configure`.

## 5) `JWT_ACCESSTOKEN_SECRET` → `conf.jwt_accesstoken_secret`

## 6) `JWT_REFRESHTOKEN_SECRET` → `conf.jwt_refreshtoken_secret`

* **What they do:** HMAC secrets for **HS**\* algorithms (e.g., HS256/HS512). Used **only** if you set `JWT_SIGNING_ALG_ACCESS`/`_REFRESH` to an HS\* alg. In prod, we recommend **asymmetric keys** instead (RS/ES/EdDSA). ([PyJWT][3])
* **Security note:** If you do use HS256, ensure the secret meets RFC 7518 sizing guidance (≥ 256 bits for HS256) to avoid brute-force risk. ([OWASP Foundation][4])

## 7) `JWT_ACCESSTOKEN_PAYLOAD_NAME` → `conf.jwt_accesstoken_payload_name`

## 8) `JWT_REFRESHTOKEN_PAYLOAD_NAME` → `conf.jwt_refreshtoken_payload_name`

* **Legacy intent (your older pattern):** A custom claim name like `access_token` / `refresh_token` as a marker in the payload.
* **How the current module handles this:**

  * The service already writes a standard `typ` claim (`"access"` or `"refresh"`) per spec, which serves the same purpose and is widely interoperable. ([IETF Datatracker][1])
  * If you still need the **legacy marker** for compatibility, just add it **on demand** using `payload_overrides`, e.g., when minting an access token include `{ conf.jwt_accesstoken_payload_name: True }`. (We intentionally **do not** hard-wire these claims to keep tokens compact and the API simple.)
* **Recommendation:** Prefer `typ` over custom markers; keep these envs only if you must maintain backward compatibility. (Registered claims are standardized; avoid name collisions.) ([Google Cloud][5])

---

# Where each old env is enforced in the flow

* **Minting (`sign_access`/`sign_refresh`)**

  * Writes: `iss` from `JWT_ISSUER`, `aud` from `JWT_AUDIENCE` (unless you override on the call), `exp/iat/jti/typ`, and whatever **extras** you pass via `payload_overrides` (e.g., `uname`, `email`, `role`, `au`, `udvc`, `sess`).
  * TTLs come from `JWT_ACCESSTOKEN_EXPIRES_IN` / `JWT_REFRESHTOKEN_EXPIRES_IN`, unless overridden per call.

* **Verification (`verify`)**

  * Validates: signature (per pinned algorithm), `iss` vs `JWT_ISSUER`, `aud` vs `JWT_AUDIENCE` (string or list), and time-based claims (`exp/iat/nbf`) with optional **leeway**. PyJWT supports issuer/audience verification and leeway explicitly. ([PyJWT][6])
  * You can further tighten **per request** by passing `aud=...`, `iss=...`, or `leeway=...` into `verify(...)`.

* **HS* secrets vs keys*\*

  * If `JWT_SIGNING_ALG_*` starts with `HS`, the corresponding `JWT_*SECRET` is used.
  * If it’s an asymmetric alg (RS/ES/EdDSA), the **PEM key paths** (new envs) are used instead; this is the recommended prod setup. ([PyJWT][3])

---

# Practical notes & best practices tied to those envs

* **Audience lists:** If your tokens may target multiple audiences, set `JWT_AUDIENCE` to a JSON list or override per call; PyJWT’s `decode` accepts an iterable for `audience`. ([PyJWT][2])
* **Leeway (clock skew):** While not one of your *old* envs, remember we support `JWT_LEEWAY`. PyJWT applies leeway to time claims; it’s useful when issuer/validator clocks drift. ([PyJWT][7])
* **Algorithm pinning:** Validation always uses a **pinned** algorithm list per token type (no `none`, no header-driven alg changes). This follows OWASP guidance against algorithm confusion. ([OWASP Foundation][8])
* **Using legacy “payload name” markers:** Prefer the standard `typ`. If you must keep the legacy keys (`access_token`, `refresh_token`), add them via `payload_overrides` only where needed to minimize token size and avoid claim collisions. (Registered claim names—`iss`, `aud`, `exp`, `iat`, `nbf`, `jti`, `sub`—shouldn’t be re-used for custom data.) ([IETF Datatracker][1])

---

## TL;DR mapping (old → now)

* **JWT\_ISSUER** → sets/validates `iss`. ✔️ Spec claim. ([IETF Datatracker][1])
* **JWT\_AUDIENCE** → sets/validates `aud` (string or list). ✔️ Spec claim. ([PyJWT][2])
* **JWT\_ACCESSTOKEN\_EXPIRES\_IN / JWT\_REFRESHTOKEN\_EXPIRES\_IN** → default TTLs (overridable). ✔️
* **JWT\_ACCESSTOKEN\_SECRET / JWT\_REFRESHTOKEN\_SECRET** → used **only** for HS\* algs; prefer keys in prod. ✔️ ([PyJWT][3])
* **JWT\_ACCESSTOKEN\_PAYLOAD\_NAME / JWT\_REFRESHTOKEN\_PAYLOAD\_NAME** → **legacy** marker keys; **not auto-inserted**; use `payload_overrides` if you still need them. Prefer `typ` (standard). ([IETF Datatracker][1])

If you want me to **auto-include** those two legacy marker claims whenever we sign (behind a toggle), say the word and I’ll add a tiny, optional flag so you don’t have to pass them manually—still keeping the code simple and fast.

[1]: https://datatracker.ietf.org/doc/html/rfc7519?utm_source=chatgpt.com "RFC 7519 - JSON Web Token (JWT)"
[2]: https://pyjwt.readthedocs.io/en/2.0.1/usage.html?utm_source=chatgpt.com "Usage Examples — PyJWT 2.0.1 documentation"
[3]: https://pyjwt.readthedocs.io/en/stable/algorithms.html?utm_source=chatgpt.com "Digital Signature Algorithms — PyJWT 2.10.1 documentation"
[4]: https://owasp.org/www-chapter-vancouver/assets/presentations/2020-01_Attacking_and_Securing_JWT.pdf?utm_source=chatgpt.com "Attacking and Securing JWT"
[5]: https://cloud.google.com/apigee/docs/api-platform/reference/policies/verify-jwt-policy?utm_source=chatgpt.com "VerifyJWT policy | Apigee"
[6]: https://pyjwt.readthedocs.io/en/stable/api.html?utm_source=chatgpt.com "API Reference — PyJWT 2.10.1 documentation - Read the Docs"
[7]: https://pyjwt.readthedocs.io/en/latest/usage.html?utm_source=chatgpt.com "Usage Examples — PyJWT 2.10.1 documentation"
[8]: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/06-Session_Management_Testing/10-Testing_JSON_Web_Tokens?utm_source=chatgpt.com "OWASP - Testing JSON Web Tokens"

