"""Validate raw model output and retry invalid structures with a second model.

Routing uses the existing JSON schema and an exact-repetition guard. It never
sees reference annotations or repairs, combines, or selects expected values.
"""

from collections import Counter
import gc
import json
import os
from pathlib import Path
import re

from .contract import messages_for, parse_output


def repeated_constraint_loop(raw):
    """Detect three identical complete constraint objects, including in partial JSON.

    Only complete array items count; braces inside quoted place names and nested
    weather conditions are handled by the JSON decoder. No answer is repaired.
    """
    prefix = re.match(r'\s*\{\s*"constraints"\s*:\s*\[', raw)
    if prefix is None:
        return False
    decoder, counts, position = json.JSONDecoder(), Counter(), prefix.end()
    while position < len(raw):
        while position < len(raw) and (raw[position].isspace() or raw[position] == ','):
            position += 1
        try:
            item, position = decoder.raw_decode(raw, position)
        except json.JSONDecodeError:
            return False
        if not isinstance(item, dict):
            return False
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        counts[key] += 1
        if counts[key] >= 3:
            return True
    return False


def extract_with_fallback(model_input, primary, fallback=None):
    attempts = []
    for role, generate in (("primary", primary), ("fallback", fallback)):
        if generate is None:
            continue
        raw = generate(model_input)
        parsed, errors = parse_output(raw)
        if repeated_constraint_loop(raw):
            parsed = None
            errors = errors + ["Generation repeated an identical constraint at least three times"]
        attempts.append({"model_role": role, "raw_output": raw, "validation_errors": errors})
        if parsed is not None:
            return {"parsed_output": parsed, "raw_output": raw, "validation_errors": [],
                    "model_used": role, "fallback_used": role == "fallback", "attempts": attempts}
    # Invalid output remains a failure, including when both models fail.
    last = attempts[-1]
    return {"parsed_output": None, "raw_output": last["raw_output"],
            "validation_errors": last["validation_errors"], "model_used": None,
            "fallback_used": len(attempts) > 1, "attempts": attempts}


class LocalExtractor:
    """Keep one model resident at a time; load MLX only for live requests."""

    def __init__(self, primary, fallback=None, max_tokens=768):
        self.primary = self._check_spec(primary)
        self.fallback = self._check_spec(fallback) if fallback else None
        self.max_tokens = max_tokens
        self._loaded = None
        self._model = self._tokenizer = None

    @staticmethod
    def _check_spec(spec):
        for key in ("model", "adapter"):
            if not Path(spec[key]).is_dir():
                raise FileNotFoundError(f"Missing {key} directory: {spec[key]}")
        if not (Path(spec["adapter"]) / "adapters.safetensors").is_file():
            raise FileNotFoundError(f"Missing adapter weights: {spec['adapter']}")
        return dict(spec)

    @classmethod
    def from_config(cls, path):
        config = json.loads(Path(path).read_text())
        return cls(config["primary"], config.get("fallback"), config.get("max_tokens", 768))

    @property
    def description(self):
        name = self.primary.get("label", "Local Transformer")
        return name + (" with schema-validated fallback" if self.fallback else "")

    def _generate(self, model_input, spec):
        # These settings also avoid the memory pressure seen during training.
        os.environ.setdefault("MLX_DISABLE_COMPILE", "1")
        os.environ.setdefault("MLX_MAX_OPS_PER_BUFFER", "8")
        os.environ.setdefault("MLX_MAX_MB_PER_BUFFER", "32")
        import mlx.core as mx
        from mlx_lm import stream_generate, load
        from mlx_lm.sample_utils import make_sampler

        mx.set_memory_limit(6 * 1024**3)
        mx.set_cache_limit(256 * 1024**2)
        key = (spec["model"], spec["adapter"])
        if key != self._loaded:
            self._model = self._tokenizer = None
            self._loaded = None
            gc.collect()
            mx.clear_cache()
            self._model, self._tokenizer = load(spec["model"], adapter_path=spec["adapter"])
            self._loaded = key
        mx.random.seed(42)
        prompt = self._tokenizer.apply_chat_template(
            messages_for({"input": model_input}), tokenize=False, add_generation_prompt=True)
        chunks = []
        stream = stream_generate(self._model, self._tokenizer, prompt=prompt,
                                 max_tokens=self.max_tokens, sampler=make_sampler(temp=0.0))
        try:
            for response in stream:
                chunks.append(response.text)
                if "}" in response.text and repeated_constraint_loop("".join(chunks)):
                    break
        finally:
            stream.close()
        return "".join(chunks)

    def extract(self, model_input):
        fallback = (lambda item: self._generate(item, self.fallback)) if self.fallback else None
        return extract_with_fallback(model_input, lambda item: self._generate(item, self.primary), fallback)
