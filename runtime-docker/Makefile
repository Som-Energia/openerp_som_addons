SHELL := /usr/bin/env bash

.PHONY: dataset-producer-create dataset-producer-dump dataset-producer-publish dataset-producer-all dataset-producer-legacy-all dataset-consumer-all dataset-consumer-prepare dataset-consumer-pull dataset-consumer-restore dataset-consumer-up dataset-smoke-vpn runtime-build-prewarmed runtime-export-prewarmed-db runtime-publish-prewarmed dataset-create dataset-dump dataset-publish dataset-pull dataset-restore

dataset-producer-create:
	bash -lc 'set -euo pipefail; [ -f .env.producer ] || { echo ".env.producer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.producer; ./scripts/producer_create_db.sh'

dataset-producer-dump:
	bash -lc 'set -euo pipefail; [ -f .env.producer ] || { echo ".env.producer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.producer; ./scripts/create_dataset.sh'

dataset-producer-publish:
	bash -lc 'set -euo pipefail; [ -f .env.producer ] || { echo ".env.producer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.producer; ./scripts/publish_dataset.sh'

dataset-producer-all: runtime-build-prewarmed dataset-producer-publish

dataset-producer-legacy-all: dataset-producer-create dataset-producer-dump dataset-producer-publish

dataset-consumer-all: dataset-consumer-prepare dataset-consumer-restore dataset-consumer-up

dataset-consumer-prepare:
	bash -lc 'set -euo pipefail; [ -f .env.consumer ] || { echo ".env.consumer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.consumer; ./scripts/consumer_prepare_assets.sh'

dataset-consumer-pull:
	bash -lc 'set -euo pipefail; [ -f .env.consumer ] || { echo ".env.consumer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.consumer; ./scripts/pull_dataset.sh'

dataset-consumer-restore:
	bash -lc 'set -euo pipefail; [ -f .env.consumer ] || { echo ".env.consumer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.consumer; ./scripts/restore_dataset.sh'

dataset-consumer-up:
	bash -lc 'set -euo pipefail; [ -f .env.consumer ] || { echo ".env.consumer is required" >&2; exit 1; }; COMPOSE_FILES="-f ./docker-compose.consumer.yml"; [ -f ./docker-compose.consumer.override.yml ] && COMPOSE_FILES="$$COMPOSE_FILES -f ./docker-compose.consumer.override.yml"; docker compose --env-file ./.env.consumer $$COMPOSE_FILES up postgres mongo redis erp-runtime'

dataset-smoke-vpn:
	bash -lc 'set -euo pipefail; [ -f .env.producer ] || { echo ".env.producer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.producer; ./scripts/smoke_test_dataset_flow.sh'

runtime-build-prewarmed:
	bash -lc 'set -euo pipefail; [ -f .env.producer ] || { echo ".env.producer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.producer; ./scripts/build_prewarmed_image.sh'

runtime-publish-prewarmed:
	bash -lc 'set -euo pipefail; [ -f .env.producer ] || { echo ".env.producer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.producer; PREWARM_ONLY_DB_EXPORT=0 EXPORT_PREWARMED_DB=0 ./scripts/build_prewarmed_image.sh'

runtime-export-prewarmed-db:
	bash -lc 'set -euo pipefail; [ -f .env.producer ] || { echo ".env.producer is required" >&2; exit 1; }; while IFS= read -r line; do case "$$line" in ""|\#*) continue;; esac; export "$$line"; done < ./.env.producer; PREWARM_ONLY_DB_EXPORT=1 EXPORT_PREWARMED_DB=1 ./scripts/build_prewarmed_image.sh'

# Backward-compatible aliases.
dataset-create: dataset-producer-dump

dataset-dump: dataset-producer-dump

dataset-publish: dataset-producer-publish

dataset-pull: dataset-consumer-pull

consumer-prepare: dataset-consumer-prepare

consumer-up: dataset-consumer-up

consumer-all: dataset-consumer-all

dataset-restore: dataset-consumer-restore
