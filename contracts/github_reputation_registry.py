
# { “Depends”: “py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6” }

from genlayer import *
import typing

class GitHubReputationRegistry(gl.Contract):
last_username: str
last_score: str

```
def __init__(self):
    self.profiles = {}
    self.last_username = ""
    self.last_score = ""

@gl.public.view
def get_profile(self, username: str) -> str:
    if username not in self.profiles:
        return "Profile not found"
    return self.profiles[username]

@gl.public.view
def get_last_username(self) -> str:
    return self.last_username

@gl.public.view
def get_last_score(self) -> str:
    return self.last_score

@gl.public.write
def analyze_profile(self, username: str) -> typing.Any:
    if username in self.profiles:
        return "Already registered"

    profile_url = "https://github.com/" + username

    def fetch_score() -> str:
        response = gl.nondet.web.get(profile_url)
        web_data = response.body.decode("utf-8")
        task = (
            "You are reviewing a GitHub developer profile for: " + username + ".\n"
            "Based on the following page content, rate this developer's activity "
            "with a single number from 1 to 100. Reply with only the number, nothing else.\n"
            "Page content:\n" + web_data[:2000]
        )
        result = gl.nondet.exec_prompt(task).strip()
        return result

    score = gl.eq_principle.strict_eq(fetch_score)
    self.profiles[username] = score
    self.last_username = username
    self.last_score = score
    return score
```
