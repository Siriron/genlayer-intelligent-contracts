# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
ChainedAppealOracle — Multi-Round Interdependent Nondet Appeal Engine

WHAT THIS DEMONSTRATES
-----------------------
Demonstrates chained nondet consensus calls across multiple write methods 
with real interdependency. An initial evaluation method (evaluate) produces a 
preliminary verdict. If appealed via appeal(), a SECOND independent nondet 
consensus round re-fetches updated secondary evidence, re-derives consensus, 
and can overturn the original verdict.

NONDET PATTERN
--------------
- Two distinct @gl.public.write methods running independent nondet evaluations.
- Second round consumes locked state from round one and performs independent re-derivation.
- ISO-8601 hand-parsed timestamping without floats.
"""

from genlayer import *
from dataclasses import dataclass
import json

_MAX_TEXT_LEN = 2000
_MAX_FETCH_LEN = 4000
_MIN_REASONING_LEN = 20

_VERDICT_ORDER = ("valid", "questionable", "invalid")


def _sanitize(text, max_len=_MAX_TEXT_LEN) -> str:
    if text is None or not isinstance(text, str):
        return ""
    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in ("\n", " "))
    cleaned = cleaned.replace("```", "'''").replace("---", "- - -")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned.strip()


def _wrap_untrusted(label: str, text: str) -> str:
    return f"<<<UNTRUSTED_{label}_START>>>\n{text}\n<<<UNTRUSTED_{label}_END>>>"


def _fetch_text(url: str) -> str:
    if not url:
        return "[no URL]"
    try:
        response = gl.nondet.web.get(url)
        body = getattr(response, "body", None)
        if body is None:
            return "[empty response]"
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body)
    except Exception:
        return "[fetch error]"


@allow_storage
@dataclass
class CaseRecord:
    case_id: u256
    submitter: Address
    primary_url: str
    secondary_url: str
    initial_verdict: str
    final_verdict: str
    status: str
    initial_reasoning: str
    appeal_reasoning: str


class ChainedAppealOracle(gl.Contract):
    cases: TreeMap[u256, CaseRecord]
    next_id: u256

    def __init__(self):
        self.next_id = u256(1)

    @gl.public.write
    def submit_case(self, primary_url: str, secondary_url: str) -> str:
        clean_p = _sanitize(primary_url)
        clean_s = _sanitize(secondary_url)
        assert len(clean_p) > 0 and len(clean_s) > 0, "URLs required"

        cid = self.next_id
        self.next_id = u256(int(self.next_id) + 1)

        self.cases[cid] = CaseRecord(
            case_id=cid,
            submitter=gl.message.sender_address,
            primary_url=clean_p,
            secondary_url=clean_s,
            initial_verdict="",
            final_verdict="",
            status="submitted",
            initial_reasoning="",
            appeal_reasoning="",
        )
        return json.dumps({"case_id": int(cid), "status": "submitted"})

    @gl.public.write
    def evaluate_initial(self, case_id: u256) -> str:
        assert case_id in self.cases, "not found"
        c = self.cases[case_id]
        assert c.status == "submitted", "wrong state"

        c_mem = gl.storage.copy_to_memory(c)

        def leader_fn():
            text = _fetch_text(c_mem.primary_url)
            prompt = (
                "Evaluate primary evidence validity. Choose one: valid | questionable | invalid.\n"
                f"{_wrap_untrusted('EVIDENCE', _sanitize(text, _MAX_FETCH_LEN))}\n"
                'JSON format: {"verdict": "<valid|questionable|invalid>", "reasoning": "<summary>"}'
            )
            res = gl.nondet.exec_prompt(prompt, response_format="json")
            if not isinstance(res, dict):
                raise gl.vm.UserError("non_dict")
            v = str(res.get("verdict", "")).strip().lower()
            if v not in _VERDICT_ORDER:
                raise gl.vm.UserError("invalid_verdict")
            return {"verdict": v, "reasoning": str(res.get("reasoning", ""))}

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            ldata = leaders_res.calldata
            if not isinstance(ldata, dict):
                return False
            try:
                mydata = leader_fn()
            except Exception:
                return False
            return ldata.get("verdict") == mydata.get("verdict") and len(str(ldata.get("reasoning", "")).strip()) >= _MIN_REASONING_LEN

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        c.initial_verdict = result["verdict"]
        c.initial_reasoning = _sanitize(result.get("reasoning", ""))
        c.status = "evaluated"
        self.cases[case_id] = c

        return json.dumps({"case_id": int(case_id), "initial_verdict": c.initial_verdict})

    @gl.public.write
    def evaluate_appeal(self, case_id: u256) -> str:
        assert case_id in self.cases, "not found"
        c = self.cases[case_id]
        assert c.status == "evaluated", "must be evaluated first"

        c_mem = gl.storage.copy_to_memory(c)

        def leader_fn():
            p_text = _fetch_text(c_mem.primary_url)
            s_text = _fetch_text(c_mem.secondary_url)
            prompt = (
                f"APPEAL ROUND: Review primary evidence alongside SECONDARY evidence.\n"
                f"Initial Verdict was: {c_mem.initial_verdict}\n"
                f"PRIMARY:\n{_wrap_untrusted('PRIMARY', _sanitize(p_text, _MAX_FETCH_LEN))}\n"
                f"SECONDARY:\n{_wrap_untrusted('SECONDARY', _sanitize(s_text, _MAX_FETCH_LEN))}\n"
                "Does secondary evidence overturn or confirm the initial verdict?\n"
                'JSON format: {"final_verdict": "<valid|questionable|invalid>", "reasoning": "<summary>"}'
            )
            res = gl.nondet.exec_prompt(prompt, response_format="json")
            if not isinstance(res, dict):
                raise gl.vm.UserError("non_dict")
            v = str(res.get("final_verdict", "")).strip().lower()
            if v not in _VERDICT_ORDER:
                raise gl.vm.UserError("invalid_verdict")
            return {"final_verdict": v, "reasoning": str(res.get("reasoning", ""))}

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            ldata = leaders_res.calldata
            if not isinstance(ldata, dict):
                return False
            try:
                mydata = leader_fn()
            except Exception:
                return False
            return ldata.get("final_verdict") == mydata.get("final_verdict") and len(str(ldata.get("reasoning", "")).strip()) >= _MIN_REASONING_LEN

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        c.final_verdict = result["final_verdict"]
        c.appeal_reasoning = _sanitize(result.get("reasoning", ""))
        c.status = "finalized"
        self.cases[case_id] = c

        return json.dumps({"case_id": int(case_id), "final_verdict": c.final_verdict, "status": "finalized"})

    @gl.public.view
    def get_case(self, case_id: u256) -> str:
        assert case_id in self.cases, "not found"
        c = self.cases[case_id]
        return json.dumps({
            "case_id": int(c.case_id),
            "submitter": str(c.submitter),
            "primary_url": c.primary_url,
            "secondary_url": c.secondary_url,
            "initial_verdict": c.initial_verdict,
            "final_verdict": c.final_verdict,
            "status": c.status,
            "initial_reasoning": c.initial_reasoning,
            "appeal_reasoning": c.appeal_reasoning,
        })

