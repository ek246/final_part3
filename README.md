# 📎 Quick Links

https://hub.docker.com/repository/docker/edocidss22/final_part1/general
## Testing
Run Docker, open Bash in the project folder, and run the following commands:
- cd module9_is601
- source venv312/bin/activate
- pip install -r requirements.txt
- docker compose up -d db
- export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_db"
- export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_test_db"
- pytest  
These commands assume that you already have the `fastapi_test_db` database created
## Documentation

documentation folder containing screenshots is included. It contains:

- Cpllection of screenshots of successful GitHub Actions and application running in browser:
[Collection of required screenshots](documentation/Module_12_screenshots.docx)
