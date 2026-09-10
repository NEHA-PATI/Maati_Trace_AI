The canonical farmer workflow is POST /v1/hot-stream/farms/{farm_id}/run-latest-analysis.
It queues one per-farm master job and runs farm readiness/H3, full-boundary Sentinel-2,
all registered environment contracts, trends, the 10 m grid/crosswalk, crop features,
and formula-backed calculated intelligence in that order. Poll
GET /v1/hot-stream/farms/{farm_id}/analysis-status for stage progress.

The individual materialize, environment-refresh, and history-backfill endpoints remain
available for diagnostics and operator backfills; they are not the normal farmer path.
