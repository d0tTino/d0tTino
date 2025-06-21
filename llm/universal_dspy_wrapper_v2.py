# Auto-generated version of LoggedFewShotWrapper (DSPy wrapper).
# This helper wraps any DSPy module and can compile it with a few-shot
# optimiser. It works even when no metric is provided by defaulting to
# dspy.LabeledFewShot.

from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path
from typing import Callable, List, Type

import dspy
from dspy.teleprompt import LabeledFewShot


class LoggedFewShotWrapper(dspy.Module):
    """Wrap any DSPy module, logging I/O and optionally compiling with a
    few-shot optimiser.
    """

    def __init__(
        self,
        wrapped: dspy.Module,
        *,
        optimiser_cls: Type = LabeledFewShot,
        optimiser_kwargs: dict | None = None,
        metric: Callable[[dspy.Prediction, dspy.Example], float] | None = None,
        log_dir: str | Path = "logs",
        fewshot_dir: str | Path = "fewshot",
    ) -> None:
        super().__init__()
        self.wrapped = wrapped
        self.optimiser_cls = optimiser_cls
        self.optimiser_kwargs = optimiser_kwargs or {}
        self.metric = metric

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.fewshot_dir = Path(fewshot_dir)
        self.fewshot_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self.log_dir / f"{wrapped.__class__.__name__}_io.jsonl"
        self._fewshot_file = self.fewshot_dir / f"{wrapped.__class__.__name__}_fewshot.jsonl"

        trainset: List[dspy.Example] = []
        if self._fewshot_file.exists():
            with self._fewshot_file.open() as fh:
                for line in fh:
                    obj = json.loads(line)
                    ex = dspy.Example(**obj.get("inputs", obj), **obj.get("outputs", {}))
                    ex = ex.with_inputs(*obj.get("inputs", obj).keys())
                    trainset.append(ex)

        optimiser_params = inspect.signature(self.optimiser_cls.__init__).parameters
        needs_metric = "metric" in optimiser_params
        can_run = bool(trainset) and (not needs_metric or self.metric)

        if can_run:
            kwargs = self.optimiser_kwargs.copy()
            if needs_metric:
                kwargs["metric"] = self.metric
            optimiser = self.optimiser_cls(**kwargs)
            self.compiled = optimiser.compile(self.wrapped, trainset=trainset)
        else:
            self.compiled = self.wrapped

        self._trainset = trainset
        self._needs_metric = needs_metric

    def snapshot_log_to_fewshot(self, replace: bool = False) -> None:
        """Copy logged data into the few-shot file."""
        if not self._log_file.exists():
            return
        mode = "w" if replace else "a"
        with self._fewshot_file.open(mode, encoding="utf-8") as out:
            with self._log_file.open(encoding="utf-8") as fh:
                shutil.copyfileobj(fh, out)

    def recompile_from_fewshot(self) -> None:
        """Reload few-shot data from file and recompile."""
        self.__init__(
            self.wrapped,
            optimiser_cls=self.optimiser_cls,
            optimiser_kwargs=self.optimiser_kwargs,
            metric=self.metric,
            log_dir=self.log_dir,
            fewshot_dir=self.fewshot_dir,
        )

    def forward(self, **inputs):
        prediction = self.compiled(**inputs)
        record = {
            "inputs": inputs,
            "outputs": getattr(prediction, "as_dict", lambda: prediction)(),
        }
        with self._log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return prediction
