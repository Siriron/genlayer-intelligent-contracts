# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
NameBind - a package name resolves to a repository only when BOTH authorities say so.

TECHNIQUE: two-authority mutual binding, evidence derived from the claimed identifiers only.
  * Authority 1, the PyPI JSON record for the package: its own name must echo the claim
    (PEP 503 normalised) and every GitHub repository named in its URLs is collected. The claim
    "points" only if the claimed repo is the SOLE repository PyPI names.
  * Authority 2, the GitHub repository: the repo id and full_name must echo the claim; the
    default branch head is resolved, pyproject.toml is read at that exact commit and its git
    blob SHA-1 is recomputed from the bytes (mismatch fails closed); the [project] or
    [tool.poetry] name must equal the claimed package.
  * State ladder, derived in code, never typed by the caller:
      BOUND         registry names this repo AND the repo's manifest names this package
      PYPI_ONLY     registry names this repo; manifest silent or different
      REPO_ONLY     manifest names the package; registry names no repo, or several
      UNLINKED      neither side makes the link
      CONTRADICTED  registry names other repositories and not this one
  * Validators re-fetch both authorities and require every field to match exactly. There is
    no model and no tolerance: both sources are structured and fully recomputed.
  * claim() is also the re-check: anyone may call it again. A later BOUND claim for the same
    package takes over the resolver pointer and marks the earlier claim superseded; a claim
    that stops being BOUND releases the pointer. resolve() reads that pointer.

Who benefits from a false verdict: a typosquatter or fork owner who publishes metadata that
points at somebody else's repository (or copies a popular manifest), and every installer or
registry mirror that would resolve the name to the wrong source.

Every state is reachable: BOUND (both), PYPI_ONLY (pointer, no manifest name), REPO_ONLY
(manifest name, registry silent or ambiguous), UNLINKED (neither), CONTRADICTED (registry
names another repo).

DELIBERATE GAPS: root pyproject.toml only (monorepo subdirectories are not resolved); PyPI
only; BOUND proves the registry project's controller and the repository's controller agree,
not that either is the original author. No clock is used.
"""

from genlayer import *
from dataclasses import dataclass
import base64
import hashlib
import json
import re

_STATES = ("BOUND", "PYPI_ONLY", "REPO_ONLY", "UNLINKED", "CONTRADICTED")
_MAX_REPOS = 8
_MAX_MANIFEST_BYTES = 60000
_SHA_RE = r"[0-9a-f]{40}"
_REPO_RE = r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}"
_PKG_RE = r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?"
_BRANCH_RE = r"[A-Za-z0-9][A-Za-z0-9._/-]{0,99}"
_GH_URL = re.compile(
    r"(?:https?://|git\+https?://|git@)(?:www\.)?github\.com[/:]([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]+)"
)
_NOT_OWNERS = ("sponsors", "orgs", "apps", "marketplace", "features", "topics", "settings")

_UNVERIFIED = {
    "evidence_ok": False, "package": "", "repo": "", "repo_id": 0, "pypi_repos": [], "head": "",
    "manifest_blob": "", "manifest_name": "", "pypi_points": False, "pypi_elsewhere": False,
    "repo_names": False, "state": "",
}


def _norm(name) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _decide(points, elsewhere, names) -> str:
    if elsewhere:
        return "CONTRADICTED"
    if points and names:
        return "BOUND"
    if points:
        return "PYPI_ONLY"
    if names:
        return "REPO_ONLY"
    return "UNLINKED"


def _http(url, allow_404=False):
    response = gl.nondet.web.get(url)
    status = getattr(response, "status", None)
    body = getattr(response, "body", None)
    if allow_404 and status == 404:
        return 404, None
    if isinstance(body, str):
        body = body.encode("utf-8")
    if status != 200 or not isinstance(body, bytes) or len(body) > 3000000:
        raise ValueError("fetch")
    return 200, json.loads(body.decode("utf-8"))


def _git_blob_sha1(raw) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def _pypi_repos(pkg) -> list:
    """GitHub repositories named by the PyPI record. Raises unless the record echoes pkg."""
    _, d = _http("https://pypi.org/pypi/" + pkg + "/json")
    info = d.get("info") if isinstance(d, dict) else None
    if not isinstance(info, dict) or not isinstance(info.get("name"), str) or _norm(info["name"]) != pkg:
        raise ValueError("pypi echo")
    urls = []
    pu = info.get("project_urls")
    if isinstance(pu, dict):
        urls.extend(v for v in pu.values() if isinstance(v, str))
    for k in ("home_page", "download_url"):
        if isinstance(info.get(k), str):
            urls.append(info[k])
    found = set()
    for u in urls:
        for m in _GH_URL.finditer(u):
            owner, name = m.group(1).lower(), m.group(2)
            if name.lower().endswith(".git"):
                name = name[:-4]
            if owner in _NOT_OWNERS or not name:
                continue
            found.add(owner + "/" + name.lower())
    if len(found) > _MAX_REPOS:
        raise ValueError("too many repos")
    return sorted(found)


def _repo_meta(repo):
    _, d = _http("https://api.github.com/repos/" + repo)
    if (
        not isinstance(d, dict) or type(d.get("id")) is not int
        or not isinstance(d.get("full_name"), str) or d["full_name"].lower() != repo
        or not isinstance(d.get("default_branch"), str) or not re.fullmatch(_BRANCH_RE, d["default_branch"])
    ):
        raise ValueError("repo envelope")
    return d["id"], d["default_branch"]


def _manifest_name(text) -> str:
    section = ""
    for line in text.split("\n"):
        m = re.match(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$", line)
        if m:
            section = m.group(1).strip()
            continue
        if section in ("project", "tool.poetry"):
            n = re.match(r"""^\s*name\s*=\s*["']([^"']+)["']""", line)
            if n:
                return _norm(n.group(1).strip())
    return ""


def _manifest(repo, branch):
    """(head_sha, blob_sha, normalised_name). blob/name are empty when pyproject.toml is absent."""
    _, b = _http("https://api.github.com/repos/" + repo + "/branches/" + branch)
    commit = b.get("commit") if isinstance(b, dict) else None
    if (
        not isinstance(b, dict) or b.get("name") != branch or not isinstance(commit, dict)
        or not isinstance(commit.get("sha"), str) or not re.fullmatch(_SHA_RE, commit["sha"])
    ):
        raise ValueError("branch echo")
    head = commit["sha"]
    status, env = _http("https://api.github.com/repos/" + repo + "/contents/pyproject.toml?ref=" + head, True)
    if status == 404:
        return head, "", ""
    if (
        not isinstance(env, dict) or env.get("type") != "file" or env.get("encoding") != "base64"
        or env.get("path") != "pyproject.toml" or not isinstance(env.get("content"), str)
        or not isinstance(env.get("sha"), str)
    ):
        raise ValueError("manifest envelope")
    raw = base64.b64decode(re.sub(r"\s+", "", env["content"]), validate=True)
    if not raw or len(raw) > _MAX_MANIFEST_BYTES:
        raise ValueError("manifest size")
    blob = _git_blob_sha1(raw)
    if blob != env["sha"]:
        raise ValueError("blob mismatch")
    return head, blob, _manifest_name(raw.decode("utf-8"))


def _collect(pkg, repo) -> dict:
    try:
        repos = _pypi_repos(pkg)
        rid, branch = _repo_meta(repo)
        head, blob, mname = _manifest(repo, branch)
    except Exception:
        return dict(_UNVERIFIED)
    points = len(repos) == 1 and repo in repos
    elsewhere = len(repos) > 0 and repo not in repos
    names = mname == pkg
    return {
        "evidence_ok": True, "package": pkg, "repo": repo, "repo_id": rid, "pypi_repos": repos,
        "head": head, "manifest_blob": blob, "manifest_name": mname, "pypi_points": points,
        "pypi_elsewhere": elsewhere, "repo_names": names, "state": _decide(points, elsewhere, names),
    }


def _well_formed(r) -> bool:
    try:
        if not isinstance(r, dict) or set(r) != set(_UNVERIFIED):
            return False
        if r["evidence_ok"] is False:
            return r == _UNVERIFIED
        if r["evidence_ok"] is not True or type(r["repo_id"]) is not int:
            return False
        if not re.fullmatch(_SHA_RE, r["head"]):
            return False
        if r["manifest_blob"] != "" and not re.fullmatch(_SHA_RE, r["manifest_blob"]):
            return False
        if r["manifest_blob"] == "" and r["manifest_name"] != "":
            return False
        repos = r["pypi_repos"]
        if not isinstance(repos, list) or len(repos) > _MAX_REPOS or repos != sorted(set(repos)):
            return False
        points = len(repos) == 1 and r["repo"] in repos
        elsewhere = len(repos) > 0 and r["repo"] not in repos
        names = r["manifest_name"] == r["package"]
        return (
            r["pypi_points"] is points and r["pypi_elsewhere"] is elsewhere and r["repo_names"] is names
            and r["state"] == _decide(points, elsewhere, names)
        )
    except Exception:
        return False


@allow_storage
@dataclass
class Claim:
    claim_id: u256
    requester: Address
    package: str
    repo: str
    repo_id: u256
    state: str
    attempts: u256
    superseded: bool
    result_json: str


class NameBind(gl.Contract):
    claims: TreeMap[u256, Claim]
    claim_index: TreeMap[str, u256]
    owners: TreeMap[str, u256]
    next_claim_id: u256

    def __init__(self):
        self.next_claim_id = u256(1)

    @gl.public.write
    def claim(self, package: str, repo: str) -> str:
        if not isinstance(package, str) or not re.fullmatch(_PKG_RE, package):
            raise gl.vm.UserError("invalid package name")
        if not isinstance(repo, str) or not re.fullmatch(_REPO_RE, repo):
            raise gl.vm.UserError("repo must be owner/name")
        pkg_mem = _norm(package)
        repo_mem = repo.lower()
        key = pkg_mem + ":" + repo_mem

        def leader_fn():
            return _collect(pkg_mem, repo_mem)

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            leader = leaders_res.calldata
            if not _well_formed(leader):
                return False
            try:
                mine = leader_fn()
            except Exception:
                return False
            return _well_formed(mine) and leader == mine

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        if not _well_formed(result):
            raise gl.vm.UserError("Invalid consensus result")
        if not result["evidence_ok"]:
            return json.dumps({"package": pkg_mem, "repo": repo_mem, "state": "UNVERIFIED"})
        if result["package"] != pkg_mem or result["repo"] != repo_mem:
            raise gl.vm.UserError("Result not bound to the claim")

        existing = self.claim_index.get(key, u256(0))
        if int(existing) > 0:
            rec = self.claims[existing]
            rec.attempts = u256(int(rec.attempts) + 1)
        else:
            cid = self.next_claim_id
            self.next_claim_id = u256(int(cid) + 1)
            rec = Claim(
                claim_id=cid, requester=gl.message.sender_address, package=pkg_mem, repo=repo_mem,
                repo_id=u256(result["repo_id"]), state="", attempts=u256(1), superseded=False, result_json="",
            )
            self.claim_index[key] = cid
        rec.repo_id = u256(result["repo_id"])
        rec.state = result["state"]
        rec.result_json = json.dumps(result, sort_keys=True)

        owner_id = self.owners.get(pkg_mem, u256(0))
        if result["state"] == "BOUND":
            if int(owner_id) > 0 and int(owner_id) != int(rec.claim_id):
                prev = self.claims[owner_id]
                prev.superseded = True
                self.claims[owner_id] = prev
            rec.superseded = False
            self.owners[pkg_mem] = rec.claim_id
        elif int(owner_id) == int(rec.claim_id):
            self.owners[pkg_mem] = u256(0)
        self.claims[rec.claim_id] = rec
        return json.dumps({"claim_id": int(rec.claim_id), "package": pkg_mem, "repo": repo_mem, "state": rec.state})

    @gl.public.view
    def resolve(self, package: str) -> str:
        pkg = _norm(package.strip())
        cid = self.owners.get(pkg, u256(0))
        if int(cid) == 0:
            return json.dumps({"bound": False, "package": pkg})
        c = self.claims[cid]
        return json.dumps({
            "bound": True, "package": pkg, "repo": c.repo, "repo_id": int(c.repo_id), "claim_id": int(cid),
        })

    @gl.public.view
    def get_claim(self, claim_id: u256) -> str:
        if claim_id not in self.claims:
            raise gl.vm.UserError("Claim not found")
        c = self.claims[claim_id]
        return json.dumps({
            "claim_id": int(c.claim_id), "requester": c.requester.as_hex, "package": c.package,
            "repo": c.repo, "repo_id": int(c.repo_id), "state": c.state, "attempts": int(c.attempts),
            "superseded": bool(c.superseded), "result": json.loads(c.result_json),
        })

    @gl.public.view
    def get_counts(self) -> str:
        return json.dumps({"claims": int(self.next_claim_id) - 1})
