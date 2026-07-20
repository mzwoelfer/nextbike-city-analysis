# Quick Test: Processor

Want to test if processing works after making changes? Use test mode.

## Run a Quick Test

Add to your `.env`:
```bash
TEST_RUN_SECONDS=300
```

Restart processor:
```bash
docker compose up -d processor
```

Watch logs:
```bash
docker compose logs -f processor
```

You'll see:
```
Test mode enabled. Running scheduled processing for 2026-07-20 in 300 seconds
Running scheduled processing for 2026-07-20
Processing city 467 for 2026-07-20
Processing city 1170 for 2026-07-20
```

## What's Happening

- **Normal mode**: Waits until midnight, processes yesterday's data
- **Test mode** (`TEST_RUN_SECONDS` set): Runs after N seconds, processes today's data

## Turn Off Test Mode

Remove from `.env`:
```bash
# TEST_RUN_SECONDS=300
```

Restart:
```bash
docker compose up -d processor
```
