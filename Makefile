.PHONY: dev db seed test clean

dev:
	docker-compose up --build

db:
	docker-compose exec backend alembic upgrade head

seed:
	docker-compose exec backend python -m scripts.seed_data || echo "No seed script found"

test:
	cd backend && pytest -v

clean:
	docker-compose down -v
	docker system prune -f
