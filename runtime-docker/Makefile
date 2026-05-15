SHELL := /usr/bin/env bash

.PHONY: dataset-producer-create dataset-producer-publish dataset-consumer-pull dataset-consumer-restore dataset-smoke-vpn runtime-build-prewarmed dataset-create dataset-publish dataset-pull dataset-restore

dataset-producer-create:
	./scripts/create_dataset.sh

dataset-producer-publish:
	./scripts/publish_dataset.sh

dataset-consumer-pull:
	./scripts/pull_dataset.sh

dataset-consumer-restore:
	./scripts/restore_dataset.sh

dataset-smoke-vpn:
	./scripts/smoke_test_dataset_flow.sh

runtime-build-prewarmed:
	./scripts/build_prewarmed_image.sh

# Backward-compatible aliases.
dataset-create: dataset-producer-create

dataset-publish: dataset-producer-publish

dataset-pull: dataset-consumer-pull

dataset-restore: dataset-consumer-restore
