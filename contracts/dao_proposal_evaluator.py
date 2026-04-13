
# { “Depends”: “py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6” }

from genlayer import *
import typing

class DAOProposalEvaluator(gl.Contract):
dao_name: str
constitution: str
last_verdict: str

```
def __init__(self, dao_name: str, constitution: str):
    self.dao_name = dao_name
    self.constitution = constitution
    self.proposals = {}
    self.verdicts = {}
    self.last_verdict = ""

@gl.public.view
def get_constitution(self) -> str:
    return self.constitution

@gl.public.view
def get_dao_name(self) -> str:
    return self.dao_name

@gl.public.view
def get_last_verdict(self) -> str:
    return self.last_verdict

@gl.public.view
def get_proposal(self, proposal_id: str) -> str:
    if proposal_id not in self.proposals:
        return "Not found"
    return self.proposals[proposal_id]

@gl.public.view
def get_verdict(self, proposal_id: str) -> str:
    if proposal_id not in self.verdicts:
        return "Not evaluated yet"
    return self.verdicts[proposal_id]

@gl.public.write
def submit_proposal(self, title: str, description: str) -> typing.Any:
    proposal_id = str(len(self.proposals))
    self.proposals[proposal_id] = title + ": " + description
    return proposal_id

@gl.public.write
def evaluate_proposal(self, proposal_id: str) -> typing.Any:
    if proposal_id not in self.proposals:
        return "Proposal not found"
    if proposal_id in self.verdicts:
        return "Already evaluated: " + self.verdicts[proposal_id]

    constitution = self.constitution
    proposal = self.proposals[proposal_id]

    def get_verdict() -> str:
        task = (
            "You are evaluating a DAO proposal for: " + self.dao_name + ".\n"
            "Constitution:\n" + constitution + "\n"
            "Proposal:\n" + proposal + "\n"
            "Does this proposal align with the constitution? "
            "Reply with exactly one word: approved, rejected, or revision."
        )
        result = gl.nondet.exec_prompt(task).strip().lower()
        if "approved" in result:
            return "approved"
        elif "rejected" in result:
            return "rejected"
        return "revision"

    verdict = gl.eq_principle.strict_eq(get_verdict)
    self.verdicts[proposal_id] = verdict
    self.last_verdict = verdict
    return verdict
```
