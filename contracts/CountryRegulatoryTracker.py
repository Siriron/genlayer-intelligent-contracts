
# { “Depends”: “py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6” }

from genlayer import *
import typing

class CountryRegulatoryTracker(gl.Contract):
country: str
topic: str
stance: str
summary: str
has_evaluated: bool

```
def __init__(self, country: str, topic: str):
    self.country = country
    self.topic = topic
    self.stance = ""
    self.summary = ""
    self.has_evaluated = False

@gl.public.view
def get_country(self) -> str:
    return self.country

@gl.public.view
def get_topic(self) -> str:
    return self.topic

@gl.public.view
def get_stance(self) -> str:
    return self.stance

@gl.public.view
def get_summary(self) -> str:
    return self.summary

@gl.public.view
def is_evaluated(self) -> bool:
    return self.has_evaluated

@gl.public.write
def evaluate(self) -> typing.Any:
    if self.has_evaluated:
        return "Already evaluated"

    country = self.country
    topic = self.topic
    query = country.replace(" ", "+") + "+" + topic.replace(" ", "+") + "+regulation+policy"
    source_url = "https://news.google.com/search?q=" + query + "&hl=en"

    def get_evaluation() -> str:
        response = gl.nondet.web.get(source_url)
        web_data = response.body.decode("utf-8")
        task = (
            "You are a regulatory policy analyst.\n"
            "Country: " + country + "\n"
            "Topic: " + topic + "\n"
            "Recent news content:\n" + web_data[:2000] + "\n\n"
            "Based on current news, what is this country's regulatory stance on this topic?\n"
            "Respond in this exact format:\n"
            "STANCE: permissive OR restrictive OR neutral OR unclear\n"
            "SUMMARY: one sentence describing the current regulatory position."
        )
        result = gl.nondet.exec_prompt(task)
        return result

    raw = gl.eq_principle.strict_eq(get_evaluation)

    stance = "unclear"
    summary = raw
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("STANCE:"):
            val = line.split(":", 1)[1].strip().lower()
            if "permissive" in val:
                stance = "permissive"
            elif "restrictive" in val:
                stance = "restrictive"
            elif "neutral" in val:
                stance = "neutral"
            else:
                stance = "unclear"
        elif line.upper().startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()

    self.stance = stance
    self.summary = summary
    self.has_evaluated = True
    return self.stance
```
