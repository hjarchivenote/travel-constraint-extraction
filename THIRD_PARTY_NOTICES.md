# Third-party sources and notices

## Qwen and LoRA artifact

Base models: [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) and [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct), Apache License 2.0. The larger comparison uses [the pinned MLX 4-bit conversion](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit). Original weights are not redistributed. The shipped adapter is a modification created by task-specific LoRA training; its license and modification notice are in artifacts/qwen05_lora/.

## London reference locations

© OpenStreetMap contributors. Data in data/reference/london_places.json is derived from the Geofabrik Greater London snapshot dated 16 October 2026 and remains under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). [OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright). The file contains source IDs, dates, original object links and centroid limitations; it asserts no current hours or availability.

## Weather snapshot

Weather data by Open-Meteo, using ECMWF IFS 0.25° forecasts, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source URL and retrieval time are embedded in data/reference/london_forecast.json. Values are stored unchanged; the demo derives a rain/dry/unknown classification at a documented 0.1 mm hourly rain-plus-showers threshold. [ECMWF data source](https://open-meteo.com/en/docs/ecmwf-api). The free API endpoint is used for this noncommercial educational prototype; future commercial API use must follow the provider terms.

## Dependencies

MLX / MLX LM, Transformers, Hugging Face Hub and jsonschema retain their respective upstream licenses. The presentation and report authoring dependencies are not required to run the model or demo.
