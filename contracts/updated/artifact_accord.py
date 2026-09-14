# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
ArtifactAccord — contested research-artifact identity and metadata review.

Practical use:
- A repository owner and a consumer lock an exact GitHub repository and
  release/tag representing a dataset, model, benchmark, or research artifact.
- The consumer opens a review against a precommitted checklist.
- The contract derives TWO independent evidence legs from the same locked
  identifier: GitHub repository metadata and the tagged release.
- Validators independently re-fetch both legs and compare the decision.
- The result is an ordered review outcome:
    PASS / MINOR_GAP / MAJOR_GAP / UNVERIFIABLE
  The ordinal ladder is meaningful: validators may differ by one rung but
  reject a two-rung disagreement.
- The review is then confirmed by the repository owner and consumer.

This is deliberately different from ReleaseAccord: it demonstrates a
graded-outcome consensus mechanism and cross-document evidence binding for
research artifacts rather than bilateral software-release acceptance.
"""

from genlayer import *
from dataclasses import dataclass
import json


MAX_TEXT = 1400
MAX_FETCH = 18000

OPEN = "open"
PASS = "pass"
MINOR_GAP = "minor_gap"
MAJOR_GAP = "major_gap"
UNVERIFIABLE = "unverifiable"

OUTCOMES = (PASS, MINOR_GAP, MAJOR_GAP, UNVERIFIABLE)


def _clean(value: str, limit: int) -> str:
    value = (value or "").strip()
    assert len(value) <= limit, "text too long"
    return value


def _repo_path(owner: str, repo: str) -> str:
    owner = _clean(owner, 120)
    repo = _clean(repo, 120)
    assert owner and repo, "owner and repo required"
    assert "/" not in owner and "/" not in repo, "invalid identifier"
    return owner.lower() + "/" + repo.lower()


def _fetch_json(url: str):
    response = gl.nondet.web.request(url, method="GET")
    status = getattr(response, "status_code", None)
    if status is not None and status >= 400:
        return {"ok": False}
    body = getattr(response, "body", None)
    if body is None:
        return {"ok": False}
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if not isinstance(body, str):
        return {"ok": False}
    try:
        return {"ok": True, "data": json.loads(body)}
    except Exception:
        return {"ok": False}


def _s(value, limit=1000) -> str:
    if value is None:
        return ""
    return str(value)[:limit]


def _rank(outcome: str) -> int:
    if outcome == PASS:
        return 0
    if outcome == MINOR_GAP:
        return 1
    if outcome == MAJOR_GAP:
        return 2
    return 3


def _agree(leader_outcome: str, own_outcome: str) -> bool:
    if leader_outcome not in OUTCOMES or own_outcome not in OUTCOMES:
        return False
    # Adjacent severity disagreement is tolerated. A two-rung swing is not.
    return abs(_rank(leader_outcome) - _rank(own_outcome)) <= 1


def _review_prompt(checklist: str, evidence: dict) -> str:
    return f"""
Review a research artifact against a precommitted checklist.

Checklist:
<checklist>{checklist}</checklist>

The evidence below was fetched from GitHub URLs deterministically derived
from the locked repository and release tag. Do not use outside assumptions.

Return JSON:
{{
  "outcome": "pass" | "minor_gap" | "major_gap" | "unverifiable",
  "reason": "short factual explanation"
}}

Outcome rules:
- pass: all material checklist requirements are supported.
- minor_gap: the artifact is substantially compliant but one non-material
  requirement is missing or unclear.
- major_gap: a material requirement is contradicted or absent.
- unverifiable: identity/evidence is missing or contradictory.
Do not invent repository facts.

Evidence:
{json.dumps(evidence, sort_keys=True)}
"""


@allow_storage
@dataclass
class Artifact:
    artifact_id: u256
    publisher: Address
    owner: str
    repo: str
    tag: str
    created_at: str


@allow_storage
@dataclass
class Review:
    review_id: u256
    artifact_id: u256
    consumer: Address
    checklist: str
    outcome: str
    reason: str
    publisher_confirmed: bool
    consumer_confirmed: bool
    created_at: str
    resolved_at: str


class ArtifactAccord(gl.Contract):
    artifacts: TreeMap[u256, Artifact]
    reviews: TreeMap[u256, Review]
    next_artifact: u256
    next_review: u256

    def __init__(self):
        self.next_artifact = u256(1)
        self.next_review = u256(1)

    @gl.public.write
    def register_artifact(self, owner: str, repo: str, tag: str) -> str:
        _repo_path(owner, repo)
        tag = _clean(tag, 180)
        assert tag, "tag required"

        aid = self.next_artifact
        self.next_artifact = u256(int(aid) + 1)
        self.artifacts[aid] = Artifact(
            aid,
            gl.message.sender_address,
            owner.strip(),
            repo.strip(),
            tag,
            gl.message_raw["datetime"],
        )
        return json.dumps({"artifact_id": int(aid), "status": "registered"})

    @gl.public.write
    def open_review(
        self,
        artifact_id: u256,
        consumer: Address,
        checklist: str,
    ) -> str:
        assert artifact_id in self.artifacts, "artifact not found"
        artifact = self.artifacts[artifact_id]
        assert artifact.publisher == gl.message.sender_address, "only publisher"
        assert consumer != artifact.publisher, "consumer must differ"

        checklist = _clean(checklist, MAX_TEXT)
        assert checklist, "checklist required"

        rid = self.next_review
        self.next_review = u256(int(rid) + 1)
        self.reviews[rid] = Review(
            rid,
            artifact_id,
            consumer,
            checklist,
            OPEN,
            "",
            False,
            False,
            gl.message_raw["datetime"],
            "",
        )
        return json.dumps({"review_id": int(rid), "status": OPEN})

    @gl.public.write
    def resolve_review(self, review_id: u256) -> str:
        assert review_id in self.reviews, "review not found"
        review = self.reviews[review_id]
        assert review.outcome == OPEN, "review already resolved"
        assert gl.message.sender_address == review.consumer, "only consumer"

        artifact = gl.storage.copy_to_memory(self.artifacts[review.artifact_id])
        checklist = review.checklist

        repo_path = _repo_path(artifact.owner, artifact.repo)
        repo_url = "https://api.github.com/repos/" + repo_path
        release_url = (
            "https://api.github.com/repos/"
            + repo_path
            + "/releases/tags/"
            + artifact.tag
        )

        def build_evidence():
            repo_result = _fetch_json(repo_url)
            release_result = _fetch_json(release_url)

            repo_data = repo_result.get("data", {})
            release_data = release_result.get("data", {})

            repo_identity = _s(repo_data.get("full_name"))
            release_tag = _s(release_data.get("tag_name"))
            release_name = _s(release_data.get("name"))
            release_target = _s(release_data.get("target_commitish"))

            identity_ok = (
                repo_result.get("ok") is True
                and release_result.get("ok") is True
                and repo_identity.lower() == repo_path
                and release_tag == artifact.tag
            )

            return {
                "identity_ok": identity_ok,
                "locked_repo": repo_path,
                "locked_tag": artifact.tag,
                "repo_full_name": repo_identity,
                "release_tag": release_tag,
                "release_name": release_name,
                "release_target": release_target,
                "repo_description": _s(repo_data.get("description"), 1800),
                "repo_license": _s(
                    (repo_data.get("license") or {}).get("spdx_id"), 200
                ),
                "release_prerelease": release_data.get("prerelease", None),
                "release_draft": release_data.get("draft", None),
            }

        def leader_fn():
            evidence = build_evidence()
            if not evidence["identity_ok"]:
                return {
                    "outcome": UNVERIFIABLE,
                    "reason": "GitHub records did not echo the locked artifact identity.",
                }

            result = gl.nondet.exec_prompt(
                _review_prompt(checklist, evidence),
                response_format="json",
            )
            if not isinstance(result, dict):
                raise gl.vm.UserError("non_dict_review_result")
            return result

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False

            leader = leaders_res.calldata
            if not isinstance(leader, dict):
                return False

            leader_outcome = leader.get("outcome")
            if leader_outcome not in OUTCOMES:
                return False

            evidence = build_evidence()
            if not evidence["identity_ok"]:
                return leader_outcome == UNVERIFIABLE

            own = gl.nondet.exec_prompt(
                _review_prompt(checklist, evidence),
                response_format="json",
            )
            if not isinstance(own, dict):
                return False

            own_outcome = own.get("outcome")
            if not _agree(leader_outcome, own_outcome):
                return False

            # The exact evidence identity fields are deterministic gates.
            # Validators therefore never accept a semantic outcome when
            # their independently fetched artifact is not the locked one.
            return bool(_s(own.get("reason"), 1800))

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        outcome = result.get("outcome")
        assert outcome in OUTCOMES, "invalid consensus outcome"

        review.outcome = outcome
        review.reason = _s(result.get("reason"), 1800)
        review.resolved_at = gl.message_raw["datetime"]

        return json.dumps({
            "review_id": int(review_id),
            "outcome": outcome,
        })

    @gl.public.write
    def confirm_review(self, review_id: u256) -> str:
        assert review_id in self.reviews, "review not found"
        review = self.reviews[review_id]
        assert review.outcome != OPEN, "review not resolved"

        artifact = self.artifacts[review.artifact_id]
        sender = gl.message.sender_address

        if sender == artifact.publisher:
            review.publisher_confirmed = True
        elif sender == review.consumer:
            review.consumer_confirmed = True
        else:
            raise gl.vm.UserError("not a review party")

        return json.dumps({
            "review_id": int(review_id),
            "publisher_confirmed": review.publisher_confirmed,
            "consumer_confirmed": review.consumer_confirmed,
        })

    @gl.public.view
    def get_artifact(self, artifact_id: u256) -> str:
        assert artifact_id in self.artifacts, "artifact not found"
        a = self.artifacts[artifact_id]
        return json.dumps({
            "artifact_id": int(a.artifact_id),
            "publisher": a.publisher.as_hex,
            "owner": a.owner,
            "repo": a.repo,
            "tag": a.tag,
            "created_at": a.created_at,
        })

    @gl.public.view
    def get_review(self, review_id: u256) -> str:
        assert review_id in self.reviews, "review not found"
        r = self.reviews[review_id]
        return json.dumps({
            "review_id": int(r.review_id),
            "artifact_id": int(r.artifact_id),
            "consumer": r.consumer.as_hex,
            "checklist": r.checklist,
            "outcome": r.outcome,
            "reason": r.reason,
            "publisher_confirmed": r.publisher_confirmed,
            "consumer_confirmed": r.consumer_confirmed,
            "created_at": r.created_at,
            "resolved_at": r.resolved_at,
        })
