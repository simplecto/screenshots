TAG:=$(shell date "+%Y%m%d%H%M")

###############################################################################
# HELP / DEFAULT COMMAND
###############################################################################
.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.PHONY: build
build: ## Build the screenshots services
	docker build -t screenshots -t screenshots:$(TAG) .

.PHONY: build-prod
build-prod: ## Build the screenshots services remotely
	docker -H screenshots build -t screenshots -t screenshots:$(TAG) .

.PHONY: prod-deploy
prod-deploy: ## deploy to production
	ssh screenshots "cd deployment/screenshots && docker-compose up -d"

.PHONY: prod-migrate
prod-migrate: ## run production migrations
	ssh root@screenshots "cd /root/deployment/screenshots && docker-compose exec web ./manage.py migrate"

