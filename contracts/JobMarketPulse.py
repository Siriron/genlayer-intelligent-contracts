
# { “Depends”: “py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6” }

from genlayer import *
import typing

class JobMarketPulse(gl.Contract):
skill: str
demand_level: str
top_roles: str
has_analyzed: bool

```
def __init__(self, skill: str):
    self.skill = skill
    self.demand_level = ""
    self.top_roles = ""
    self.has_analyzed = False

@gl.public.view
def get_skill(self) -> str:
    return self.skill

@gl.public.view
def get_demand_level(self) -> str:
    return self.demand_level

@gl.public.view
def get_top_roles(self) -> str:
    return self.top_roles

@gl.public.view
def is_analyzed(self) -> bool:
    return self.has_analyzed

@gl.public.write
def analyze(self) -> typing.Any:
    if self.has_analyzed:
        return "Already analyzed"

    skill = self.skill
    source_url = "https://remoteok.com/remote-" + skill.lower().replace(" ", "-") + "-jobs"

    def get_analysis() -> str:
        response = gl.nondet.web.get(source_url)
        web_data = response.body.decode("utf-8")
        task = (
            "You are a job market analyst.\n"
            "Skill being analyzed: " + skill + "\n"
            "Job board data:\n" + web_data[:2000] + "\n\n"
            "Based on this data, assess the current remote job market demand for this skill.\n"
            "Respond in this exact format:\n"
            "DEMAND: high OR medium OR low\n"
            "ROLES: comma-separated list of up to 3 job titles that most commonly require this skill"
        )
        result = gl.nondet.exec_prompt(task)
        return result

    raw = gl.eq_principle.strict_eq(get_analysis)

    demand_level = "unknown"
    top_roles = ""
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("DEMAND:"):
            val = line.split(":", 1)[1].strip().lower()
            if "high" in val:
                demand_level = "high"
            elif "medium" in val:
                demand_level = "medium"
            elif "low" in val:
                demand_level = "low"
        elif line.upper().startswith("ROLES:"):
            top_roles = line.split(":", 1)[1].strip()

    self.demand_level = demand_level
    self.top_roles = top_roles
    self.has_analyzed = True
    return self.demand_level
```
