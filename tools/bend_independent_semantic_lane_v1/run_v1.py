"""Run the Bend independent semantic lane V1.

State slice: bend-independent-semantic-lane-v1.

The Rust example owns case generation and expected local outcomes. This module
only renders the frozen executable subset into Bend syntax, runs Bend in an
external temporary directory, and compares aggregate observations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

STATE_SLICE = "bend-independent-semantic-lane-v1"
PROTOCOL_IDENTITY = "bend-independent-semantic-lane-v1"
BEND_VERSION = "2.0.4"
DEFAULT_SEEDS = 32
DEFAULT_STRESS_DEPTH = 14
REPO_ROOT = Path(__file__).resolve().parents[2]


class LaneError(RuntimeError):
    """A fail-closed lane error."""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_digests() -> dict[str, str]:
    return {
        "rust_exporter": _sha256_file(
            REPO_ROOT / "crates/zkbench-core/examples/bend_export_v1.rs"
        ),
        "python_driver": _sha256_file(Path(__file__).resolve()),
    }


def _nat(value: int) -> str:
    if value < 0:
        raise LaneError(f"negative natural value is outside Bend V1: {value}")
    return f"{value}n"


def _bool(value: bool) -> str:
    return "True{}" if value else "False{}"


def _list(values: list[str]) -> str:
    return "[" + ", ".join(values) + "]"


def _value(value: dict[str, Any]) -> str:
    kind = value["kind"]
    if kind == "Int":
        return f"VInt{{{_nat(int(value['value']))}}}"
    if kind == "Bool":
        return f"VBool{{{_bool(bool(value['value']))}}}"
    raise LaneError(f"unsupported exported value kind: {kind}")


def _operand(operand: dict[str, Any]) -> str:
    kind = operand["kind"]
    if kind == "Field":
        return f"FieldOp{{{_nat(int(operand['field']))}}}"
    if kind == "Literal":
        return f"LiteralOp{{{_value(operand['value'])}}}"
    raise LaneError(f"unsupported exported operand kind: {kind}")


def _guard(guard: dict[str, Any]) -> str:
    kind = guard["kind"]
    if kind == "Bool":
        return f"Always{{}}" if guard["value"] else "Never{}"
    if kind in {"Eq", "Neq", "Lt", "Lte", "Gt", "Gte"}:
        constructor = {
            "Eq": "GEq",
            "Neq": "GNeq",
            "Lt": "GLt",
            "Lte": "GLte",
            "Gt": "GGt",
            "Gte": "GGte",
        }[kind]
        return f"{constructor}{{{_operand(guard['left'])}, {_operand(guard['right'])}}}"
    if kind == "And":
        items = [_guard(item) for item in guard["items"]]
        if not items:
            return "Always{}"
        result = items[0]
        for item in items[1:]:
            result = f"GAnd{{{result}, {item}}}"
        return result
    if kind == "Or":
        items = [_guard(item) for item in guard["items"]]
        if not items:
            return "Never{}"
        result = items[0]
        for item in items[1:]:
            result = f"GOr{{{result}, {item}}}"
        return result
    if kind == "Not":
        return f"GNot{{{_guard(guard['item'])}}}"
    raise LaneError(f"unsupported exported guard kind: {kind}")


def _action(action: dict[str, Any]) -> str:
    kind = action["kind"]
    if kind == "Noop":
        return "Noop{}"
    if kind in {"Assign", "AddAssign", "SubAssign"}:
        constructor = {
            "Assign": "Assign",
            "AddAssign": "AddAssign",
            "SubAssign": "SubAssign",
        }[kind]
        return f"{constructor}{{{_nat(int(action['field']))}, {_operand(action['value'])}}}"
    raise LaneError(f"unsupported exported action kind: {kind}")


def _assignment(assignment: dict[str, Any]) -> str:
    return f"Assignment{{{_nat(int(assignment['field']))}, {_value(assignment['value'])}}}"


def _machine(machine: dict[str, Any]) -> str:
    initial_fields = _list([_value(value) for value in machine["initial_fields"]])
    transitions = _list(
        [
            "Transition{{{from_state}, {to_state}, {guard}, {actions}}}".format(
                from_state=_nat(int(transition["from"])),
                to_state=_nat(int(transition["to"])),
                guard=_guard(transition["guard"]),
                actions=_list([_action(action) for action in transition["actions"]]),
            )
            for transition in machine["transitions"]
        ]
    )
    invariants = _list([_guard(guard) for guard in machine["invariants"]])
    return (
        f"Machine{{{_nat(int(machine['initial_state']))}, {initial_fields}, "
        f"{transitions}, {invariants}}}"
    )


def _trace(trace: dict[str, Any], machine: dict[str, Any]) -> str:
    expected_state = (
        "None{}"
        if trace["expected_final_state"] is None
        else f"Some{{{_nat(int(trace['expected_final_state']))}}}"
    )
    transitions = machine["transitions"]
    step_transitions: list[str] = []
    for raw_step in trace["steps"]:
        step = int(raw_step)
        if step < 0 or step >= len(transitions):
            raise LaneError(f"trace references missing transition {step}")
        transition = transitions[step]
        step_transitions.append(
            "Transition{{{from_state}, {to_state}, {guard}, {actions}}}".format(
                from_state=_nat(int(transition["from"])),
                to_state=_nat(int(transition["to"])),
                guard=_guard(transition["guard"]),
                actions=_list([_action(action) for action in transition["actions"]]),
            )
        )
    return (
        f"Trace{{{_nat(int(trace['initial_state']))}, "
        f"{_list([_assignment(item) for item in trace['initial_fields']])}, "
        f"{_list(step_transitions)}, "
        f"{expected_state}, "
        f"{_list([_assignment(item) for item in trace['expected_final_fields']])}}}"
    )


def _case(case: dict[str, Any]) -> str:
    return f"Case{{{_machine(case['machine'])}, {_trace(case['trace'], case['machine'])}}}"


def render_suite(suite: dict[str, Any], stress_depth: int = DEFAULT_STRESS_DEPTH) -> str:
    """Render a generated suite without embedding Rust expected outcomes."""

    if suite.get("state_slice") != STATE_SLICE:
        raise LaneError("suite state slice mismatch")
    if suite.get("protocol_identity") != PROTOCOL_IDENTITY:
        raise LaneError("suite protocol identity mismatch")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise LaneError("suite has no cases")
    expected_codes = [case.get("expected_code") for case in cases]
    if any(code not in {0, 1, 2, 3} for code in expected_codes):
        raise LaneError("suite contains an invalid Rust outcome code")
    rendered_cases = [_case(case) for case in cases]
    return f"""import Base

type Value is Data:
  VInt{{value: Nat}}
  VBool{{value: Bool}}

type Operand is Data:
  FieldOp{{field: Nat}}
  LiteralOp{{value: Value}}

type Guard is Data:
  Always{{}}
  Never{{}}
  GEq{{left: Operand, right: Operand}}
  GNeq{{left: Operand, right: Operand}}
  GLt{{left: Operand, right: Operand}}
  GLte{{left: Operand, right: Operand}}
  GGt{{left: Operand, right: Operand}}
  GGte{{left: Operand, right: Operand}}
  GAnd{{left: Guard, right: Guard}}
  GOr{{left: Guard, right: Guard}}
  GNot{{item: Guard}}

type Action is Data:
  Noop{{}}
  Assign{{field: Nat, value: Operand}}
  AddAssign{{field: Nat, value: Operand}}
  SubAssign{{field: Nat, value: Operand}}

type Assignment is Data:
  Assignment{{field: Nat, value: Value}}

type Transition is Data:
  Transition{{from: Nat, to: Nat, guard: Guard, actions: List<&2, Action>}}

type Machine is Data:
  Machine{{initial_state: Nat, initial_fields: List<&2, Value>, transitions: List<&2, Transition>, invariants: List<&2, Guard>}}

type Trace is Data:
  Trace{{initial_state: Nat, initial_fields: List<&2, Assignment>, steps: List<&2, Transition>, expected_state: Maybe<&2, Nat>, expected_fields: List<&2, Assignment>}}

type Case is Data:
  Case{{machine: Machine, trace: Trace}}

type GuardResult is Data:
  GTrue{{}}
  GFalse{{}}
  GGap{{}}

type StepResult is Data:
  SContinue{{state: Nat, fields: List<&2, Value>}}
  SRejected{{}}
  SGap{{}}

type RunMode is Data:
  Running{{steps: List<&2, Transition>, state: Nat, fields: List<&2, Value>, invariants: List<&2, Guard>}}
  CheckState{{from: Nat, to: Nat, guard: Guard, actions: List<&2, Action>, rest: List<&2, Transition>, state: Nat, fields: List<&2, Value>, invariants: List<&2, Guard>}}
  StateChecked{{matched: Bool, to: Nat, guard: Guard, actions: List<&2, Action>, rest: List<&2, Transition>, fields: List<&2, Value>, invariants: List<&2, Guard>}}
  CheckGuard{{guard: Guard, to: Nat, actions: List<&2, Action>, rest: List<&2, Transition>, fields: List<&2, Value>, invariants: List<&2, Guard>}}
  GuardChecked{{result: GuardResult, to: Nat, actions: List<&2, Action>, rest: List<&2, Transition>, fields: List<&2, Value>, invariants: List<&2, Guard>}}
  ApplyActions{{actions: List<&2, Action>, to: Nat, rest: List<&2, Transition>, fields: List<&2, Value>, invariants: List<&2, Guard>}}
  ActionsApplied{{next_fields: List<&2, Value>, to: Nat, rest: List<&2, Transition>, invariants: List<&2, Guard>}}
  InvariantChecked{{result: GuardResult, next_fields: List<&2, Value>, to: Nat, rest: List<&2, Transition>, invariants: List<&2, Guard>}}

def bool_guard(value: Bool) -> GuardResult:
  match value:
    case False{{}}:
      GFalse{{}}
    case True{{}}:
      GTrue{{}}

def negate_guard(value: GuardResult) -> GuardResult:
  match value:
    case GFalse{{}}:
      GTrue{{}}
    case GTrue{{}}:
      GFalse{{}}
    case GGap{{}}:
      GGap{{}}

def value_equal(left: Value, right: Value) -> Bool:
  match left right:
    case VInt{{a}} VInt{{b}}:
      Nat.is_eq(a, b)
    case VBool{{a}} VBool{{b}}:
      Cmp.is_eq(Bool.cmp(a, b))
    case VInt{{_}} VBool{{_}}:
      False{{}}
    case VBool{{_}} VInt{{_}}:
      False{{}}

def read_value(fields: List<&2, Value>, index: Nat) -> Value:
  match fields index:
    case Nil{{}} _:
      VInt{{0n}}
    case h <> t 0n:
      h
    case h <> t 1n+p:
      read_value(t, p)

def eval_operand(operand: Operand, +fields: List<&2, Value>) -> Value:
  match operand:
    case FieldOp{{field}}:
      read_value(fields, field)
    case LiteralOp{{value}}:
      value

def eq_result(left: Value, right: Value) -> GuardResult:
  bool_guard(value_equal(left, right))

def neq_result(left: Value, right: Value) -> GuardResult:
  negate_guard(eq_result(left, right))

def and_result(left: GuardResult, right: GuardResult) -> GuardResult:
  match left:
    case GFalse{{}}:
      GFalse{{}}
    case GGap{{}}:
      GGap{{}}
    case GTrue{{}}:
      right

def or_result(left: GuardResult, right: GuardResult) -> GuardResult:
  match left right:
    case GTrue{{}} _:
      GTrue{{}}
    case GFalse{{}} result:
      result
    case GGap{{}} GTrue{{}}:
      GTrue{{}}
    case GGap{{}} _:
      GGap{{}}

def lt_result(left: Value, right: Value) -> GuardResult:
  match left right:
    case VInt{{a}} VInt{{b}}:
      bool_guard(Nat.is_lt(a, b))
    case _ _:
      GGap{{}}

def lte_result(left: Value, right: Value) -> GuardResult:
  match left right:
    case VInt{{a}} VInt{{b}}:
      bool_guard(Nat.is_le(a, b))
    case _ _:
      GGap{{}}

def gt_result(left: Value, right: Value) -> GuardResult:
  match left right:
    case VInt{{a}} VInt{{b}}:
      bool_guard(Nat.is_gt(a, b))
    case _ _:
      GGap{{}}

def gte_result(left: Value, right: Value) -> GuardResult:
  match left right:
    case VInt{{a}} VInt{{b}}:
      bool_guard(Nat.is_ge(a, b))
    case _ _:
      GGap{{}}

def eval_guard(guard: Guard, +fields: List<&2, Value>) -> GuardResult:
  match guard:
    case Always{{}}:
      GTrue{{}}
    case Never{{}}:
      GFalse{{}}
    case GEq{{left, right}}:
      eq_result(eval_operand(left, fields), eval_operand(right, fields))
    case GNeq{{left, right}}:
      neq_result(eval_operand(left, fields), eval_operand(right, fields))
    case GLt{{left, right}}:
      lt_result(eval_operand(left, fields), eval_operand(right, fields))
    case GLte{{left, right}}:
      lte_result(eval_operand(left, fields), eval_operand(right, fields))
    case GGt{{left, right}}:
      gt_result(eval_operand(left, fields), eval_operand(right, fields))
    case GGte{{left, right}}:
      gte_result(eval_operand(left, fields), eval_operand(right, fields))
    case GAnd{{left, right}}:
      and_result(eval_guard(left, fields), eval_guard(right, fields))
    case GOr{{left, right}}:
      or_result(eval_guard(left, fields), eval_guard(right, fields))
    case GNot{{item}}:
      negate_guard(eval_guard(item, fields))

def add_value(left: Value, right: Value) -> Value:
  match left right:
    case VInt{{a}} VInt{{b}}:
      VInt{{Nat.add(a, b)}}
    case _ _:
      VInt{{0n}}

def sub_value(left: Value, right: Value) -> Value:
  match left right:
    case VInt{{a}} VInt{{b}}:
      VInt{{Nat.sub(a, b)}}
    case _ _:
      VInt{{0n}}

def apply_action(action: Action, +fields: List<&2, Value>) -> List<&2, Value>:
  match action:
    case Noop{{}}:
      fields
    case Assign{{field, value}}:
      List.set(&2, Value, fields, field, eval_operand(value, fields))
    case AddAssign{{+field, value}}:
      List.set(&2, Value, fields, field, add_value(read_value(fields, field), eval_operand(value, fields)))
    case SubAssign{{+field, value}}:
      List.set(&2, Value, fields, field, sub_value(read_value(fields, field), eval_operand(value, fields)))

def apply_actions(actions: List<&2, Action>, +fields: List<&2, Value>) -> List<&2, Value>:
  match actions:
    case Nil{{}}:
      fields
    case h <> t:
      apply_actions(t, apply_action(h, fields))

def eval_invariants(invariants: List<&2, Guard>, +fields: List<&2, Value>) -> GuardResult:
  match invariants:
    case Nil{{}}:
      GTrue{{}}
    case h <> t:
      and_result(eval_guard(h, fields), eval_invariants(t, fields))

def run_fuel(steps: List<&2, Transition>) -> Nat:
  match steps:
    case Nil{{}}:
      1n
    case _ <> rest:
      Nat.add(9n, run_fuel(rest))

def run_steps(fuel: Nat, mode: RunMode) -> StepResult:
  match fuel:
    case 0n:
      SGap{{}}
    case 1n+p:
      match mode:
        case Running{{steps, state, fields, invariants}}:
          match steps:
            case Nil{{}}:
              SContinue{{state, fields}}
            case Transition{{from, to, guard, actions}} <> rest:
              run_steps(p, CheckState{{from, to, guard, actions, rest, state, fields, invariants}})
        case CheckState{{from, to, guard, actions, rest, state, fields, invariants}}:
          run_steps(p, StateChecked{{Nat.is_eq(from, state), to, guard, actions, rest, fields, invariants}})
        case StateChecked{{matched, to, guard, actions, rest, fields, invariants}}:
          match matched:
            case False{{}}:
              SRejected{{}}
            case True{{}}:
              run_steps(p, CheckGuard{{guard, to, actions, rest, fields, invariants}})
        case CheckGuard{{guard, to, actions, rest, +fields, invariants}}:
          run_steps(p, GuardChecked{{eval_guard(guard, fields), to, actions, rest, fields, invariants}})
        case GuardChecked{{result, to, actions, rest, fields, invariants}}:
          match result:
            case GFalse{{}}:
              SRejected{{}}
            case GGap{{}}:
              SGap{{}}
            case GTrue{{}}:
              run_steps(p, ApplyActions{{actions, to, rest, fields, invariants}})
        case ApplyActions{{actions, to, rest, fields, invariants}}:
          run_steps(p, ActionsApplied{{apply_actions(actions, fields), to, rest, invariants}})
        case ActionsApplied{{+next_fields, to, rest, +invariants}}:
          run_steps(p, InvariantChecked{{eval_invariants(invariants, next_fields), next_fields, to, rest, invariants}})
        case InvariantChecked{{result, next_fields, to, rest, invariants}}:
          match result:
            case GFalse{{}}:
              SRejected{{}}
            case GGap{{}}:
              SGap{{}}
            case GTrue{{}}:
              run_steps(p, Running{{rest, to, next_fields, invariants}})

def expected_state_result(expected: Maybe<&2, Nat>, actual: Nat) -> GuardResult:
  match expected:
    case None{{}}:
      GTrue{{}}
    case Some{{wanted}}:
      bool_guard(Nat.is_eq(wanted, actual))

def expected_fields_result(expected: List<&2, Assignment>, +fields: List<&2, Value>) -> GuardResult:
  match expected:
    case Nil{{}}:
      GTrue{{}}
    case Assignment{{field, value}} <> rest:
      and_result(
        bool_guard(value_equal(read_value(fields, field), value)),
        expected_fields_result(rest, fields)
      )

def finish_fields(result: GuardResult) -> Nat:
  match result:
    case GTrue{{}}:
      0n
    case GFalse{{}}:
      1n
    case GGap{{}}:
      2n

def finish_continue(state_result: GuardResult, expected_fields: List<&2, Assignment>, +fields: List<&2, Value>) -> Nat:
  match state_result:
    case GFalse{{}}:
      1n
    case GGap{{}}:
      2n
    case GTrue{{}}:
      finish_fields(expected_fields_result(expected_fields, fields))

def finish_result(result: StepResult, expected: Maybe<&2, Nat>, expected_fields: List<&2, Assignment>) -> Nat:
  match result:
    case SRejected{{}}:
      1n
    case SGap{{}}:
      2n
    case SContinue{{state, fields}}:
      finish_continue(expected_state_result(expected, state), expected_fields, fields)

def apply_overrides(overrides: List<&2, Assignment>, +fields: List<&2, Value>) -> List<&2, Value>:
  match overrides:
    case Nil{{}}:
      fields
    case Assignment{{field, value}} <> rest:
      apply_overrides(rest, List.set(&2, Value, fields, field, value))

def eval_case(case_value: Case) -> Nat:
  match case_value:
    case Case{{Machine{{initial_state, initial_fields, transitions, invariants}}, Trace{{trace_state, overrides, +steps, expected, expected_fields}}}}:
      finish_result(
        run_steps(run_fuel(steps), Running{{steps, trace_state, apply_overrides(overrides, initial_fields), invariants}}),
        expected,
        expected_fields
      )

def encode_results(cases: List<Case>, +index: Nat) -> String:
  match cases:
    case Nil{{}}:
      ""
    case h <> t:
      Nat.show(index) ++ ":" ++ Nat.show(eval_case(h)) ++ "\\n" ++ encode_results(t, Nat.add(index, 1n))

def stress_tree(+n: Nat) -> Nat:
  match n:
    case 0n:
      1n
    case 1n+p:
      a b = stress_tree(p) stress_tree(p)
      Nat.add(a, b)

def cases() -> List<Case>:
  {_list(rendered_cases)}

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(encode_results(cases(), 0n) ++ "stress:" ++ Nat.show(stress_tree({_nat(stress_depth)})))
"""


def render_laws() -> str:
    return """import Base
import ./suite.bend as Suite

law always_guard_is_true:
  {Suite.eval_guard(Suite.Always{}, []) == Suite.GTrue{} : Suite.GuardResult}

law never_guard_is_false:
  {Suite.eval_guard(Suite.Never{}, []) == Suite.GFalse{} : Suite.GuardResult}

law no_op_preserves_empty_fields:
  {Suite.apply_action(Suite.Noop{}, []) == [] : List<&2, Suite.Value>}
"""


def render_proof() -> str:
    return """import Base
import ./LAWS.bend as Laws
import ./suite.bend as Suite

def Laws.always_guard_is_true():
  {==}

def Laws.never_guard_is_false():
  {==}

def Laws.no_op_preserves_empty_fields():
  {==}

def main() -> IO(Unit):
  Suite.main()
"""


def _bend_path() -> str:
    configured = os.environ.get("BEND_BIN")
    path = configured or shutil.which("bend")
    if not path:
        raise LaneError("Bend is not available; set BEND_BIN or add Bend to PATH")
    version = subprocess.run(
        [path, "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    observed_version = version.split()[-1] if version.split() else ""
    if observed_version != BEND_VERSION:
        raise LaneError(f"expected Bend {BEND_VERSION}, observed {version!r}")
    return path


def _export(seeds: int) -> bytes:
    command = [
        "cargo",
        "run",
        "-p",
        "zkbench-core",
        "--example",
        "bend_export_v1",
        "--quiet",
        "--",
        "--seeds",
        str(seeds),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, check=True, capture_output=True)
    if not result.stdout.strip():
        raise LaneError("Rust exporter emitted no suite")
    return result.stdout


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        stdout = result.stdout.decode("utf-8", errors="replace")
        raise LaneError(
            f"command failed with exit {result.returncode}: {' '.join(command)}\n"
            f"stderr:\n{stderr}\nstdout:\n{stdout}"
        )
    return result


def _parse_output(output: bytes, expected_codes: list[int], stress_depth: int) -> tuple[list[int], str]:
    lines = output.decode("utf-8").splitlines()
    if len(lines) != len(expected_codes) + 1:
        raise LaneError(
            f"Bend emitted {len(lines)} lines; expected {len(expected_codes) + 1}"
        )
    observed: list[int] = []
    for index, line in enumerate(lines[:-1]):
        parts = line.split(":")
        if len(parts) != 2 or parts[0] != str(index) or parts[1] not in {"0", "1", "2", "3"}:
            raise LaneError(f"malformed Bend result line {index}: {line!r}")
        observed.append(int(parts[1]))
    expected_stress = str(1 << stress_depth)
    if lines[-1] != f"stress:{expected_stress}":
        raise LaneError(f"fork-join stress mismatch: {lines[-1]!r}")
    digest = hashlib.sha256(
        "\n".join(f"{index}:{code}" for index, code in enumerate(observed)).encode("utf-8")
    ).hexdigest()
    return observed, digest


def run_lane(seeds: int, stress_depth: int) -> dict[str, Any]:
    bend = _bend_path()
    first_export = _export(seeds)
    second_export = _export(seeds)
    if first_export != second_export:
        raise LaneError("Rust exporter is not byte-deterministic")
    suite = json.loads(first_export)
    expected_codes = [int(case["expected_code"]) for case in suite["cases"]]
    if not expected_codes or any(code != 0 and code != 1 for code in expected_codes):
        raise LaneError("generated corpus contains an unexpected outcome category")

    expected_digest = hashlib.sha256(
        "\n".join(f"{index}:{code}" for index, code in enumerate(expected_codes)).encode("utf-8")
    ).hexdigest()
    suite_digest = hashlib.sha256(first_export).hexdigest()
    environment = os.environ.copy()
    environment["BEND_NO_TELEMETRY"] = "1"
    with tempfile.TemporaryDirectory(prefix="bend-independent-semantic-lane-v1-") as directory:
        root = Path(directory)
        (root / "suite.bend").write_text(render_suite(suite, stress_depth), encoding="utf-8")
        (root / "LAWS.bend").write_text(render_laws(), encoding="utf-8")
        (root / "PROOF.bend").write_text(render_proof(), encoding="utf-8")

        js_started = time.monotonic()
        js_result = _run([bend, "PROOF.bend"], cwd=root, env=environment)
        js_ms = round((time.monotonic() - js_started) * 1000, 3)
        js_observed, js_digest = _parse_output(js_result.stdout, expected_codes, stress_depth)

        binary = root / "bend_suite"
        build_started = time.monotonic()
        _run([bend, "PROOF.bend", "-o", str(binary)], cwd=root, env=environment)
        build_ms = round((time.monotonic() - build_started) * 1000, 3)

        native_outputs: dict[int, bytes] = {}
        native_timings: dict[int, float] = {}
        for threads in (1, 4, 1):
            started = time.monotonic()
            result = _run([str(binary), "--threads", str(threads)], cwd=root, env=environment)
            native_timings[threads] = round((time.monotonic() - started) * 1000, 3)
            if threads not in native_outputs:
                native_outputs[threads] = result.stdout
            elif native_outputs[threads] != result.stdout:
                raise LaneError(f"native repeat differs for --threads {threads}")

        native_observed, native_digest = _parse_output(
            native_outputs[1], expected_codes, stress_depth
        )
        threaded_observed, threaded_digest = _parse_output(
            native_outputs[4], expected_codes, stress_depth
        )

    if js_observed != expected_codes:
        raise LaneError("Bend JavaScript backend differs from Rust outcomes")
    if native_observed != expected_codes:
        raise LaneError("Bend native backend differs from Rust outcomes")
    if threaded_observed != expected_codes:
        raise LaneError("Bend four-thread backend differs from Rust outcomes")
    if len({expected_digest, js_digest, native_digest, threaded_digest}) != 1:
        raise LaneError("aggregate outcome digests disagree")

    return {
        "state_slice": STATE_SLICE,
        "protocol_identity": PROTOCOL_IDENTITY,
        "bend_version": BEND_VERSION,
        "generator_families": suite["generator_families"],
        "seeds_per_family": suite["seeds_per_family"],
        "case_count": len(expected_codes),
        "accepted_count": expected_codes.count(0),
        "rejected_count": expected_codes.count(1),
        "outcome_digest": expected_digest,
        "suite_digest": suite_digest,
        "source_digests": _source_digests(),
        "js_runtime_ms": js_ms,
        "native_build_ms": build_ms,
        "native_threads_1_ms": native_timings[1],
        "native_threads_4_ms": native_timings[4],
        "stress_depth": stress_depth,
        "stress_leaves": 1 << stress_depth,
        "export_repeatable": True,
        "js_matches_rust": True,
        "native_matches_rust": True,
        "thread_repeatable": True,
        "status": "PASS",
        "claim_ceiling": "LocalBendCheckedSemanticOracleOnly",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--stress-depth", type=int, default=DEFAULT_STRESS_DEPTH)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 128:
        parser.error("--seeds must be between 1 and 128")
    if not 1 <= args.stress_depth <= 18:
        parser.error("--stress-depth must be between 1 and 18")
    try:
        print(json.dumps(run_lane(args.seeds, args.stress_depth), sort_keys=True))
    except (LaneError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"bend-independent-semantic-lane-v1: FAIL: {error}") from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
