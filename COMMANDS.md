## 🐳 Docker Deployment

rm -rf generated
python auto_sentinel.py --api https://rickandmortyapi.com/graphql --format graphql
cd generated

python -c "import app"
uvicorn app:app

docker build -t rickmorty-validator:1.0.0 .
docker run -d -p 8765:8000 rickmorty-validator:1.0.0