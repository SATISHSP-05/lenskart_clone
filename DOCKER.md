# Containerizing the Lenskart clone

1. **Build the image**  
   ```bash
   docker compose build
   ```
   This installs the Python dependencies from `requirements.txt`, copies the project into `/app/backend`, and runs `collectstatic` once during the build.

2. **Start the stack locally**  
   ```bash
   docker compose up
   ```
   The Django app is served by Gunicorn on port `8000`. Static files are collected into a named volume so they survive container restarts.

3. **Environment variables**  
   The Compose file already loads `backend/.env`. Keep secrets (API keys, database URLs) only in that `.env`; do **not** commit any production credentials. Compose mounts the project directory so code changes are reflected immediately during development.

4. **Useful commands**
   - `docker compose logs -f web` to stream Gunicorn logs.
   - `docker compose exec web python manage.py migrate` when you want to run migrations.
   - `docker compose run --rm web python manage.py shell` for an interactive shell.

5. **Production notes**
   - For deployment you can push the built image to a registry (ECR, Docker Hub) and run it on EC2 or ECS.
   - Replace SQLite with RDS/Postgres and configure storage (S3 for media) before going live.
