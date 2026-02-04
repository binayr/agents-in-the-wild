import json
import os
from typing import Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from config import logger
from agents.sparky.PyConverterAgent import spark_convert, spark_export
from agents.sparky.EvaluationAgent import evaluate
from agents.sparky.ImprovementAgent import spark_improve
from agents.sparky.base_utils import path_to_content_dict


class PySparkState(TypedDict, total=False):
    input_code: str
    converted_files: List[Dict[str, str]]
    converted_code: str
    improvements: List[str]
    score: float
    reason: str
    iteration: int
    target_score: float
    max_iters: int
    out_path: str


def _route_after_evaluate(state: PySparkState) -> str:
    target = float(state.get("target_score", 90.0))
    max_iters = int(state.get("max_iters", 3))
    score = float(state.get("score", 0.0))
    iteration = int(state.get("iteration", 0))

    if score >= target:
        logger.info(
            f"😎 Target score reached ({score:.2f} >= {target:.2f}). Finishing pipeline."
        )
        return "export"
    if iteration >= max_iters:
        logger.info(
            f"🫥 Max iterations reached ({iteration} >= {max_iters}). Finishing pipeline."
        )
        return "export"
    return "improve"


_builder = StateGraph(PySparkState)
_builder.add_node("convert", spark_convert)
_builder.add_node("evaluate", evaluate)
_builder.add_node("improve", spark_improve)
_builder.add_node("export", spark_export)

_builder.set_entry_point("convert")
_builder.add_edge("convert", "evaluate")
_builder.add_conditional_edges(
    "evaluate", _route_after_evaluate, {"improve": "improve", "export": "export"}
)
_builder.add_edge("improve", "evaluate")
_builder.add_edge("export", END)

pyspark_graph = _builder.compile()


def run_pyspark_conversion(
    path: str, target_score: float = 90.0, max_iters: int = 2
) -> PySparkState:
    """
    Execute the convert → evaluate → improve loop until target score or max iterations.
    Returns the final state containing converted files and evaluation data.
    """

    code = path_to_content_dict(path)
    outpath = path.split("/")[-1]

    for f in code:
        logger.info(f"Processing {f}")
        initial_state: PySparkState = {
            "input_code": {f: code[f]},
            "target_score": float(target_score),
            "max_iters": int(max_iters),
            "iteration": 0,
            "out_path": os.path.join(outpath, f)
        }
        pyspark_graph.invoke(initial_state)
