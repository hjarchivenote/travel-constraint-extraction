# London, Replanned

This local demo displays constraints extracted from a reference itinerary and an English change request. The planner applies illustrative edits.

Follow the [setup commands](../README.md#run-the-demo), then open <http://127.0.0.1:8765>. **Saved model run** replays an actual validation prediction from the earlier study. Use the first combined example to inspect extracted conditions. Select **Rain scenario** to replace the outdoor walk with a book-cafe category, or **Dry scenario** to keep it.

On Apple Silicon, run `configure_live.py` after installing the full requirements. **Live local model** uses the improved Qwen2.5-1.5B adapter with the smaller 0.5B fallback. Editing the request selects live mode. The first live request loads the model. No paid language-model API is required.

Forecast mode uses the timestamped London snapshot. Refresh can fetch new forecast data; dates without coverage leave the weather unresolved. The demo does not verify route feasibility, opening hours, availability, or walking caps. Nearby distances are straight-line estimates.
