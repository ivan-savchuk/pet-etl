
.PHONY: help
help:
	@echo "make linter"
	@echo "       Run linter"
	@echo "make test"
	@echo "make build-lambda"
	@echo "       Build lambda package"
	@echo "make deploy-lambda"
	@echo "       Deploy lambda package"
	@echo "make build-glue-job"
	@echo "       Build glue job package"
	@echo "make deploy-glue-job"
	@echo "       Deploy glue job package"

.PHONY: linter-common
linter-common:
	@echo "-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-"
	@echo "Running linter for common"
	@echo "-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-"
	PYTHONPATH="./common/src" pylint $(shell git ls-files 'common/src/*.py') \
		--rcfile ./.pylintrc \
		--output-format='text' --msg-template='{abspath}:{line}:{column}:{msg_id}: ({msg}) ({symbol})'

.PHONY: linter-lambda
linter-lambda:
	@echo ""
	@echo "-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-"
	@echo "Running linter for lambdas"
	@echo "-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-"
	@if [ "$(OS)" = "win" ]; \
	then \
		PYTHONPATH="./lambdas/youtube-parser/src;./common/src" pylint $(shell git ls-files 'lambdas/$(LAMBDA_DIR)/*.py') \
			--rcfile ./.pylintrc \
			--output-format='text' --msg-template='{abspath}:{line}:{column}:{msg_id}: ({msg}) ({symbol})'; \
	else \
		PYTHONPATH="./lambdas/youtube-parser/src:./common/src" pylint $(shell git ls-files 'lambdas/$(LAMBDA_DIR)/*.py') \
			--rcfile ./.pylintrc \
			--output-format='text' --msg-template='{abspath}:{line}:{column}:{msg_id}: ({msg}) ({symbol})'; \
	fi

.PYTHON: linter-glue
linter-glue:
	@echo ""
	@echo "-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-"
	@echo "Running linter for glue"
	@echo "-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-"
	@if [ "$(OS)" = "win" ]; \
	then \
		PYTHONPATH="./glue/jobs/data-transform/src;./common/src" pylint $(shell git ls-files 'glue/jobs/data-transform/src/*.py') \
			--rcfile ./.pylintrc \
			--output-format='text' --msg-template='{abspath}:{line}:{column}:{msg_id}: ({msg}) ({symbol})'; \
	else \
		PYTHONPATH="./glue/jobs/data-transform/src:./common/src" pylint $(shell git ls-files 'glue/jobs/data-transform/src/*.py') \
			--rcfile ./.pylintrc \
			--output-format='text' --msg-template='{abspath}:{line}:{column}:{msg_id}: ({msg}) ({symbol})'; \
	fi

.PHONY: linter
linter:
	@echo "Running linter"
	$(MAKE) linter-common && \
	$(MAKE) linter-lambda && \
	$(MAKE) linter-glue

.PHONY: test
test:
	@echo "Running tests"

.PHONY: build-lambda
build-lambda:
	@echo "Building $(LAMBDA_NAME) zip package"
	cd lambdas; \
	cd $(LAMBDA_DIR); \
	mkdir -p deployment; \
	pip install --upgrade --target ./deployment -r requirements.txt; \
	cp -r ../../common/src/* ./deployment/; \
	cp -r ./src/* ./deployment/; \
	cd deployment; 7z a ../$(LAMBDA_DIR).zip * -r; cd ..;

.PHONY: clean-lambda-dir
clean-lambda-dir:
	cd lambdas; \
	cd $(LAMBDA_DIR); \
	rm -rf deployment; \
	rm -rf $(LAMBDA_DIR).zip

.PHONY: deploy-lambda
deploy-lambda: build-lambda
	@echo "Deploying $(LAMBDA_NAME) lambda zip package"
	cd lambdas; \
	cd $(LAMBDA_DIR); \
	aws lambda update-function-code \
		--function-name $(LAMBDA_NAME) \
		--zip-file "fileb://$(LAMBDA_DIR).zip" \
		> deployment/code-output.json
	make clean-lambda-dir LAMBDA_DIR=$(LAMBDA_DIR)

.PHONY: build-glue-job
build-glue-job:
	@echo "Building glue job package"

.PHONY: deploy-glue-job
deploy-glue-job:
	@echo "Deploying lambda package"

.PHONY: create-cdbs
create-cdbs:
	@echo "Creating PetETLComputeDBStorage CloudFormation stack"
	aws cloudformation deploy --stack-name PetETLComputeDBStorage \
	  --template-file infra/compute-databse-storage-formation.yaml \
	  --parameter-overrides DBPassword=$(PG_PASSWORD) \
	  --profile default

.PHONY: delete-cdbs
delete-cdbs:
	@echo "Deleting PetETLComputeDBStorage CloudFormation stack"
	aws cloudformation delete-stack --stack-name PetETLComputeDBStorage \
	  --profile default

.PHONY: create-backend
create-backend:
	@echo "Creating PetETLBackend CloudFormation stack"
	aws cloudformation deploy --stack-name PetETLBackend \
	  --template-file infra/application-backend-formation.yaml \
	  --capabilities CAPABILITY_NAMED_IAM \
	  --profile default

.PHONY: delete-backend
delete-backend:
	@echo "Deleting PetETLBackend CloudFormation stack"
	aws cloudformation delete-stack --stack-name PetETLBackend \
	  --profile default