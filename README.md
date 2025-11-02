1. Create a Virtual Environment

python -m venv swvenv


2. Activate the virtual environment:

.\swvenv\Scripts\activate

3. Run the Application

uvicorn app.main:app --reload

# Docker Build Command

docker build -t sceneweaver-backend .

# Docker Full Image name

us-central1-docker.pkg.dev/sceneweaver-1/sceneweaver-services/backend:latest


postgresql+pg8000://sceneweaver_app_user:mySecurePassword123@/sceneweaver-mvp-db?unix_sock=/cloudsql/sceneweaver-1:us-central1:sceneweaver-pg-db/.s.PGSQL.5432

postgresql+pg8000://sceneweaver_app_user:SceneweaverAppUserPass#10@10.36.48.3:5432/sceneweaver-mvp-db
