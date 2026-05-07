.PHONY: dev test clean

dev:
	./start.sh

test:
	cd backend && pytest -v

clean:
	rm -rf backend/__pycache__ backend/app/__pycache__ frontend/dist
