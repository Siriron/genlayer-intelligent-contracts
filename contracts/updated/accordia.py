# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Accordia — evidence-bound software release acceptance.

Practical use:
- A publisher locks an exact GitHub repository + release tag.
- An integrator locks an acceptance policy before evaluation.
- The contract derives evidence URLs from those identifiers; callers cannot
  choose arbitrary evidence URLs.
- GenLayer independently fetches GitHub release/repository evidence and
  judges the locked policy.
- Both publisher and integrator must ratify the resulting assessment before
  it becomes ACTIVE.
- A later accepted accord can supersede the earlier one.

This is intentionally not a copy of Handshake/Treaty. It borrows the useful
ideas of immutable versions, independent semantic evaluation, bilateral
ratification, and supersession, but applies them to software release
acceptance with identifier-bound evidence.
"""

from genlayer import *
from dataclasses import dataclass
import json


MAX_TEXT = 1200
MAX_FETCH = 18000

POLICY_DRAFT = "draft"
POLICY_PUBLISHED = "published"

ASSESSMENT_OPEN = "open"
ASSESSMENT_ACCEPTED = "accepted"
ASSESSMENT_REJECTED = "rejected"
ASSESSMENT_UNVERIFIABLE = "unverifiable"

ACCORD_PROPOSED = "proposed"
ACCORD_PUBLISHER_OK = "publisher_ok"
ACCORD_ACTIVE = "active"
ACCORD_SUPERSEDED = "superseded"


def _clean(value: str, limit: int) -> str:
    value = (value or "").strip()
    assert len(value) <= limit, "text too long"
    return value


def _repo_key(owner: str, repo: str) -> str:
    owner = _clean(owner, 120)
    repo = _clean(repo, 120)
    assert owner and repo, "owner/repo required"
    assert "/" not in owner and "/" not in repo, "invalid github identifier"
    return owner.lower() + "/" + repo.lower()


def _tag(tag: str) -> str:
    tag = _clean(tag, 180)
    assert tag, "release tag required"
    return tag


def _github_api(url: str):
    response = gl.nondet.web.request(url, method="GET")
    status = getattr(response, "status_code", None)
    if status is not None and status >= 400:
        return {"ok": False, "status": status}
    body = getattr(response, "body", None)
    if body is None:
        return {"ok": False, "status": 0}
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if not isinstance(body, str):
        return {"ok": False, "status": 0}
    try:
        return {"ok": True, "data": json.loads(body)}
    except Exception:
        return {"ok": False, "status": 0}


def _safe_str(value, limit=1000) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:limit]


def _policy_prompt(policy_text: str, evidence: dict) -> str:
    return f"""
You are evaluating a software release acceptance policy.

The policy was locked before this evaluation:
<policy>{policy_text}</policy>

The evidence was fetched by the contract from GitHub URLs derived from the
locked repository owner/name and release tag. Do not invent facts outside
the evidence.

Return JSON only:
{{
  "verdict": "accept" | "reject" | "unverifiable",
  "reason": "short factual explanation",
  "policy_checks": "short semicolon-separated list of decisive checks"
}}

Rules:
1. ACCEPT only when the evidence supports the policy.
2. REJECT when the evidence clearly contradicts a required condition.
3. UNVERIFIABLE when the required evidence is missing or contradictory.
4. Never treat the caller's policy text as evidence.
5. Never assume an identifier match unless the fetched records themselves
   echo the repository/release identity.

Evidence:
{json.dumps(evidence, sort_keys=True)}
"""


@allow_storage
@dataclass
class Release:
    release_id: u256
    publisher: Address
    owner: str
    repo: str
    tag: str
    created_at: str


@allow_storage
@dataclass
class Policy:
    policy_id: u256
    owner: Address
    text: str
    version: u256
    state: str
    created_at: str


@allow_storage
@dataclass
class Assessment:
    assessment_id: u256
    release_id: u256
    policy_id: u256
    publisher: Address
    integrator: Address
    verdict: str
    reason: str
    checks: str
    assessed_at: str


@allow_storage
@dataclass
class Accord:
    accord_id: u256
    assessment_id: u256
    publisher: Address
    integrator: Address
    publisher_ok: bool
    integrator_ok: bool
    state: str
    created_at: str
    supersedes: u256


class Accordia(gl.Contract):
    releases: TreeMap[u256, Release]
    policies: TreeMap[u256, Policy]
    assessments: TreeMap[u256, Assessment]
    accords: TreeMap[u256, Accord]
    active_by_pair: TreeMap[str, u256]
    next_release: u256
    next_policy: u256
    next_assessment: u256
    next_accord: u256

    def __init__(self):
        self.next_release = u256(1)
        self.next_policy = u256(1)
        self.next_assessment = u256(1)
        self.next_accord = u256(1)

    @gl.public.write
    def register_release(self, owner: str, repo: str, tag: str) -> str:
        rid = self.next_release
        self.next_release = u256(int(rid) + 1)
        self.releases[rid] = Release(
            rid,
            gl.message.sender_address,
            owner.strip(),
            repo.strip(),
            _tag(tag),
            gl.message_raw["datetime"],
        )
        return json.dumps({"release_id": int(rid), "status": "registered"})

    @gl.public.write
    def create_policy(self, text: str) -> str:
        clean = _clean(text, MAX_TEXT)
        assert clean, "policy required"
        pid = self.next_policy
        self.next_policy = u256(int(pid) + 1)
        self.policies[pid] = Policy(
            pid,
            gl.message.sender_address,
            clean,
            u256(1),
            POLICY_DRAFT,
            gl.message_raw["datetime"],
        )
        return json.dumps({"policy_id": int(pid), "status": POLICY_DRAFT})

    @gl.public.write
    def publish_policy(self, policy_id: u256) -> str:
        assert policy_id in self.policies, "policy not found"
        p = self.policies[policy_id]
        assert p.owner == gl.message.sender_address, "only policy owner"
        assert p.state == POLICY_DRAFT, "policy already published"
        p.state = POLICY_PUBLISHED
        return json.dumps({"policy_id": int(policy_id), "status": POLICY_PUBLISHED})

    @gl.public.write
    def open_assessment(
        self,
        release_id: u256,
        policy_id: u256,
        integrator: Address,
    ) -> str:
        assert release_id in self.releases, "release not found"
        assert policy_id in self.policies, "policy not found"

        release = self.releases[release_id]
        policy = self.policies[policy_id]

        assert release.publisher == gl.message.sender_address, "only publisher"
        assert policy.state == POLICY_PUBLISHED, "policy not published"
        assert integrator != release.publisher, "integrator must differ"
        assert integrator != Address("0x0000000000000000000000000000000000000000"), "bad integrator"

        aid = self.next_assessment
        self.next_assessment = u256(int(aid) + 1)
        self.assessments[aid] = Assessment(
            aid,
            release_id,
            policy_id,
            release.publisher,
            integrator,
            ASSESSMENT_OPEN,
            "",
            "",
            "",
        )
        return json.dumps({"assessment_id": int(aid), "status": ASSESSMENT_OPEN})

    @gl.public.write
    def resolve_assessment(self, assessment_id: u256) -> str:
        assert assessment_id in self.assessments, "assessment not found"
        assessment = self.assessments[assessment_id]
        assert assessment.verdict == "", "assessment already resolved"
        assert gl.message.sender_address == assessment.integrator, "only integrator"

        release = gl.storage.copy_to_memory(self.releases[assessment.release_id])
        policy = gl.storage.copy_to_memory(self.policies[assessment.policy_id])

        repo_path = _repo_key(release.owner, release.repo)
        release_url = (
            "https://api.github.com/repos/"
            + repo_path
            + "/releases/tags/"
            + release.tag
        )
        repo_url = "https://api.github.com/repos/" + repo_path

        def leader_fn():
            release_result = _github_api(release_url)
            repo_result = _github_api(repo_url)

            release_data = release_result.get("data", {})
            repo_data = repo_result.get("data", {})

            release_name = _safe_str(release_data.get("name"))
            release_tag = _safe_str(release_data.get("tag_name"))
            release_target = _safe_str(release_data.get("target_commitish"))
            repo_full = _safe_str(repo_data.get("full_name"))
            repo_default = _safe_str(repo_data.get("default_branch"))
            repo_private = repo_data.get("private", None)

            identity_ok = (
                release_result.get("ok") is True
                and repo_result.get("ok") is True
                and release_tag == release.tag
                and repo_full.lower() == repo_path
            )

            evidence = {
                "locked_repo": repo_path,
                "locked_tag": release.tag,
                "release_identity_ok": identity_ok,
                "release_tag": release_tag,
                "release_name": release_name,
                "release_target": release_target,
                "repo_full_name": repo_full,
                "repo_default_branch": repo_default,
                "repo_private": repo_private,
            }

            if not identity_ok:
                return {
                    "verdict": ASSESSMENT_UNVERIFIABLE,
                    "reason": "GitHub evidence did not echo the locked repository/release identifiers.",
                    "policy_checks": "identifier_binding",
                }

            result = gl.nondet.exec_prompt(
                _policy_prompt(policy.text, evidence),
                response_format="json",
            )
            if not isinstance(result, dict):
                raise gl.vm.UserError("non_dict_policy_result")
            return result

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False

            leader = leaders_res.calldata
            if not isinstance(leader, dict):
                return False
            if leader.get("verdict") not in (
                ASSESSMENT_ACCEPTED,
                ASSESSMENT_REJECTED,
                ASSESSMENT_UNVERIFIABLE,
            ):
                return False

            release_result = _github_api(release_url)
            repo_result = _github_api(repo_url)
            release_data = release_result.get("data", {})
            repo_data = repo_result.get("data", {})

            release_tag = _safe_str(release_data.get("tag_name"))
            repo_full = _safe_str(repo_data.get("full_name"))

            identity_ok = (
                release_result.get("ok") is True
                and repo_result.get("ok") is True
                and release_tag == release.tag
                and repo_full.lower() == repo_path
            )
            if not identity_ok:
                return leader.get("verdict") == ASSESSMENT_UNVERIFIABLE

            evidence = {
                "locked_repo": repo_path,
                "locked_tag": release.tag,
                "release_identity_ok": True,
                "release_tag": release_tag,
                "release_name": _safe_str(release_data.get("name")),
                "release_target": _safe_str(release_data.get("target_commitish")),
                "repo_full_name": repo_full,
                "repo_default_branch": _safe_str(repo_data.get("default_branch")),
                "repo_private": repo_data.get("private", None),
            }

            own = gl.nondet.exec_prompt(
                _policy_prompt(policy.text, evidence),
                response_format="json",
            )
            if not isinstance(own, dict):
                return False

            return (
                own.get("verdict") == leader.get("verdict")
                and _clean(_safe_str(own.get("reason")), 2000)
                and _clean(_safe_str(own.get("policy_checks")), 2000)
            )

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        verdict = result.get("verdict", ASSESSMENT_UNVERIFIABLE)
        assert verdict in (
            ASSESSMENT_ACCEPTED,
            ASSESSMENT_REJECTED,
            ASSESSMENT_UNVERIFIABLE,
        )

        assessment.verdict = verdict
        assessment.reason = _safe_str(result.get("reason"), 1800)
        assessment.checks = _safe_str(result.get("policy_checks"), 1800)
        assessment.assessed_at = gl.message_raw["datetime"]

        return json.dumps({
            "assessment_id": int(assessment_id),
            "verdict": verdict,
        })

    @gl.public.write
    def propose_accord(self, assessment_id: u256) -> str:
        assert assessment_id in self.assessments, "assessment not found"
        a = self.assessments[assessment_id]
        assert a.verdict == ASSESSMENT_ACCEPTED, "only accepted assessments"
        assert gl.message.sender_address == a.publisher, "only publisher"

        pair = a.publisher.as_hex.lower() + "|" + a.integrator.as_hex.lower()
        previous = self.active_by_pair.get(pair, u256(0))

        aid = self.next_accord
        self.next_accord = u256(int(aid) + 1)

        self.accords[aid] = Accord(
            aid,
            assessment_id,
            a.publisher,
            a.integrator,
            False,
            False,
            ACCORD_PROPOSED,
            gl.message_raw["datetime"],
            previous,
        )
        return json.dumps({"accord_id": int(aid), "status": ACCORD_PROPOSED})

    @gl.public.write
    def ratify_accord(self, accord_id: u256) -> str:
        assert accord_id in self.accords, "accord not found"
        accord = self.accords[accord_id]
        sender = gl.message.sender_address

        if sender == accord.publisher:
            accord.publisher_ok = True
        elif sender == accord.integrator:
            accord.integrator_ok = True
        else:
            raise gl.vm.UserError("not a party to accord")

        if accord.publisher_ok and accord.integrator_ok:
            pair = accord.publisher.as_hex.lower() + "|" + accord.integrator.as_hex.lower()
            previous = self.active_by_pair.get(pair, u256(0))
            if previous != u256(0) and previous in self.accords:
                self.accords[previous].state = ACCORD_SUPERSEDED
            accord.state = ACCORD_ACTIVE
            self.active_by_pair[pair] = accord_id
        else:
            accord.state = (
                ACCORD_PUBLISHER_OK if accord.publisher_ok else ACCORD_PROPOSED
            )

        return json.dumps({
            "accord_id": int(accord_id),
            "publisher_ok": accord.publisher_ok,
            "integrator_ok": accord.integrator_ok,
            "status": accord.state,
        })

    @gl.public.view
    def get_release(self, release_id: u256) -> str:
        assert release_id in self.releases, "release not found"
        r = self.releases[release_id]
        return json.dumps({
            "release_id": int(r.release_id),
            "publisher": r.publisher.as_hex,
            "owner": r.owner,
            "repo": r.repo,
            "tag": r.tag,
            "created_at": r.created_at,
        })

    @gl.public.view
    def get_policy(self, policy_id: u256) -> str:
        assert policy_id in self.policies, "policy not found"
        p = self.policies[policy_id]
        return json.dumps({
            "policy_id": int(p.policy_id),
            "owner": p.owner.as_hex,
            "text": p.text,
            "version": int(p.version),
            "state": p.state,
            "created_at": p.created_at,
        })

    @gl.public.view
    def get_assessment(self, assessment_id: u256) -> str:
        assert assessment_id in self.assessments, "assessment not found"
        a = self.assessments[assessment_id]
        return json.dumps({
            "assessment_id": int(a.assessment_id),
            "release_id": int(a.release_id),
            "policy_id": int(a.policy_id),
            "publisher": a.publisher.as_hex,
            "integrator": a.integrator.as_hex,
            "verdict": a.verdict,
            "reason": a.reason,
            "checks": a.checks,
            "assessed_at": a.assessed_at,
        })

    @gl.public.view
    def get_accord(self, accord_id: u256) -> str:
        assert accord_id in self.accords, "accord not found"
        a = self.accords[accord_id]
        return json.dumps({
            "accord_id": int(a.accord_id),
            "assessment_id": int(a.assessment_id),
            "publisher": a.publisher.as_hex,
            "integrator": a.integrator.as_hex,
            "publisher_ok": a.publisher_ok,
            "integrator_ok": a.integrator_ok,
            "state": a.state,
            "created_at": a.created_at,
            "supersedes": int(a.supersedes),
        })

    @gl.public.view
    def get_active_accord(self, publisher: str, integrator: str) -> str:
        pair = publisher.strip().lower() + "|" + integrator.strip().lower()
        aid = self.active_by_pair.get(pair, u256(0))
        if aid == u256(0):
            return json.dumps({"active": False})
        return json.dumps({
            "active": True,
            "accord_id": int(aid),
            "state": self.accords[aid].state,
        })
