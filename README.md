# Module 10 Secure User Model and Calculator

This project extends the FastAPI Calculator with PostgreSQL-backed user registration,
SQLAlchemy 2 models, Pydantic input and output schemas, Argon2id password hashing,
and a test, build, scan, and Docker Hub publishing pipeline.

## Repository and Docker Hub

- GitHub: https://github.com/knj5/module10_is601
- Docker Hub: https://hub.docker.com/r/knj5/module10-calculator

Before submission, run `python3 scripts/configure_dockerhub.py YOUR_USERNAME`
to replace the Docker Hub link with your account name. This changes documentation
only. The GitHub Actions repository variable described below must also be set.

## Original implementation and attribution

The calculator operations, HTML template, and original calculator tests originated
in the MIT-licensed course starter at https://github.com/kaw393939/module9_is601.
Its license is retained. Module 9 history is kept in this separate repository.

The Module 10 implementation adds app/database.py, app/models.py, app/schemas.py,
app/security.py, app/users.py, and the corresponding schema, hashing, and PostgreSQL
tests. main.py, Docker configuration, fixtures, and CI/CD are updated to integrate
the new behavior. This submission includes a substantive implementation beyond the
unchanged instructor starter. Review these modules to understand the design.

## Start locally on a Mac

Open Docker Desktop, then run these commands from this project folder:

```bash
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8010/health
```

- Calculator: http://localhost:8010
- API documentation: http://localhost:8010/docs
- pgAdmin: http://localhost:5051 (admin@example.com / module10admin)
- pgAdmin PostgreSQL registration: host db, port 5432, database module10_db,
  username postgres, password module10local.

These credentials are for the local classroom environment. Ports bind only to the
local machine. Production credentials belong in environment configuration or a
secret manager. Database credentials and passwords must not be logged.

Module 10 has its own Compose project name, ports, and volumes. Module 9's
containers, database, repository, and submission link remain separate. No Mac
source-folder mount is used, avoiding the earlier file input/output issue.

## Register a user

```bash
curl -i http://localhost:8010/users \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","password":"ClassroomPass123!"}'
```

This is a demonstration password, not a real account credential. A successful
request returns HTTP 201 and id, username, email, and created_at. It never returns
password or password_hash. Reusing a username or email returns HTTP 409.
Invalid registration input returns HTTP 422 without echoing submitted passwords.
Existing calculator validation retains its HTTP 400 behavior.

The server creates tables on startup. The users table includes an integer primary
key, unique non-null username and email, a required password_hash, and a
timezone-aware created_at timestamp set by PostgreSQL. Password hashes are not
unique: different users may choose the same password, while individual salts
still produce different hashes. Usernames and emails are trimmed and lowercased
before insertion. Usernames contain 3-50 lowercase letters, digits, or underscores;
passwords contain 12-128 characters. EmailStr validates email structure.

Password verification is implemented in app/security.py and tested against correct,
incorrect, long Unicode, and malformed-hash cases. Authentication sessions and
authorization are beyond this module's registration requirements.

## Run tests locally with Docker

No local Python installation is needed for the unit and integration tests:

```bash
docker compose --profile test run --build --rm test
```

This starts an isolated real PostgreSQL test database and runs unit tests plus
integration tests. There is no SQLite substitute and database tests are not
silently skipped. The test database is named module10_test and is distinct from
module10_db. The test fixtures use an outer transaction and savepoints to roll
back each test, including tests that commit or encounter uniqueness failures.

To also run the browser tests inside the test image:

```bash
docker compose --profile test run --build --rm --user root test sh -c \
  'python -m playwright install --with-deps chromium && python -m pytest'
```

Browser tests use port 8765 within the test container and wait for displayed
results, avoiding timing-dependent assertions. GitHub Actions runs all three test
groups, including the browser tests.

### Optional local Python environment

Use Python 3.12. Start a dedicated local PostgreSQL test database first. The
database name must end in _test; never use your application or Module 9 database.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
export TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/module10_test'
export DATABASE_URL="$TEST_DATABASE_URL"
python -m pytest
```

Use your own test credentials in that connection string. Unit-only tests do not
need PostgreSQL: `python -m pytest tests/unit`.

## CI/CD and Docker Hub setup

1. Create your own GitHub repository named module10_is601 and push this project.
2. In Docker Hub, create the public repository module10-calculator.
3. In Docker Hub account settings, create a personal access token with Read and
   Write permission. Do not commit it or put it in the README.
4. In GitHub Settings > Secrets and variables > Actions > Variables, add the
   repository variable DOCKERHUB_USERNAME with your Docker Hub username.
5. Under the Secrets tab, add DOCKERHUB_TOKEN with that token as its value.
6. Run scripts/configure_dockerhub.py with your username, commit, and push main.
7. Check GitHub Actions. Both the test job and build/scan/deploy job must succeed.

On pushes and pull requests, the workflow runs all tests using a PostgreSQL 16
service container. After tests pass, it builds the runtime image, scans it with
Grype, and smoke-tests that same image against PostgreSQL. The scanner blocks on
High or Critical vulnerabilities with an available fix. It does not suppress a
failed scan or claim that an image has no unfixed vulnerabilities.

For successful main-branch pushes or manual main-branch runs, the workflow logs in
to Docker Hub and pushes the tested, scanned image with latest and the full Git
commit SHA tags. Pull requests never receive registry credentials or publish.
If account configuration is missing, deployment fails with a clear message.
Check actual workflow results; code alone does not demonstrate a deployment.

The runtime image runs as a non-root user and contains application dependencies.
The separate test build stage adds test tools. The image health check uses Python
and validates a live PostgreSQL connection, with no curl dependency inside the image.

## Pull and run the published image

After a successful Docker Hub push:

```bash
docker pull --platform linux/amd64 knj5/module10-calculator:latest
docker compose up -d db
docker run --rm --platform linux/amd64 --network module10_is601_default \
  -p 127.0.0.1:8011:8000 \
  -e DATABASE_URL=postgresql+psycopg://postgres:module10local@db:5432/module10_db \
  knj5/module10-calculator:latest
```

Open http://localhost:8011/health in another window. These commands use the local
classroom database. For a deployed environment, supply that environment's database
URL instead. The published image targets linux/amd64, matching the GitHub runner. ARM Macs use Docker Desktop emulation with the platform flags above.

## Evidence for submission

Include your GitHub repository link, the actual Docker Hub repository link, a
screenshot of the successful GitHub Actions run, a screenshot of the published
Docker Hub tags, and a reflection on the implementation and challenges actually
encountered. The final reflection and deployment evidence are completed after
the live workflow succeeds.

Schema creation uses SQLAlchemy create_all for a new classroom database. It does
not migrate the Module 9 users table or alter existing schemas. Future schema
changes should use migrations such as Alembic.

## Technical references

- FastAPI hashing: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- SQLAlchemy testing transactions: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/
- GitHub PostgreSQL services: https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers
- Grype scanning action: https://github.com/anchore/scan-action
