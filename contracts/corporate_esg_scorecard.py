# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import typing


class CorporateESGScorecard(gl.Contract):
    company: str
    environmental: str
    social: str
    governance: str
    overall: str
    summary: str
    has_evaluated: bool

    def __init__(self, company: str):
        self.company = company
        self.environmental = ""
        self.social = ""
        self.governance = ""
        self.overall = ""
        self.summary = ""
        self.has_evaluated = False

    @gl.public.view
    def get_company(self) -> str:
        return self.company

    @gl.public.view
    def get_environmental(self) -> str:
        return self.environmental

    @gl.public.view
    def get_social(self) -> str:
        return self.social

    @gl.public.view
    def get_governance(self) -> str:
        return self.governance

    @gl.public.view
    def get_overall(self) -> str:
        return self.overall

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

        company = self.company
        source_url = (
            "https://news.google.com/rss/search?q="
            + company.replace(" ", "+")
            + "+ESG+sustainability+environment+social+governance&hl=en-US&gl=US&ceid=US:en"
        )

        def get_evaluation() -> str:
            response = gl.nondet.web.get(source_url)
            web_data = response.body.decode("utf-8")
            task = (
                "You are a professional ESG analyst.\n"
                "Company: " + company + "\n"
                "Live news feed:\n" + web_data[:2000] + "\n\n"
                "Based on this data, evaluate the company's ESG standing.\n"
                "Respond in this exact format:\n"
                "ENVIRONMENTAL: poor OR fair OR good OR excellent\n"
                "SOCIAL: poor OR fair OR good OR excellent\n"
                "GOVERNANCE: poor OR fair OR good OR excellent\n"
                "OVERALL: poor OR fair OR good OR excellent\n"
                "SUMMARY: one sentence describing the company's overall ESG standing"
            )
            result = gl.nondet.exec_prompt(task)
            return result

        raw = gl.eq_principle.strict_eq(get_evaluation)

        environmental = "unknown"
        social = "unknown"
        governance = "unknown"
        overall = "unknown"
        summary = ""

        valid_ratings = ["poor", "fair", "good", "excellent"]

        for line in raw.splitlines():
            line = line.strip()
            if line.upper().startswith("ENVIRONMENTAL:"):
                val = line.split(":", 1)[1].strip().lower()
                for r in valid_ratings:
                    if r in val:
                        environmental = r
                        break
            elif line.upper().startswith("SOCIAL:"):
                val = line.split(":", 1)[1].strip().lower()
                for r in valid_ratings:
                    if r in val:
                        social = r
                        break
            elif line.upper().startswith("GOVERNANCE:"):
                val = line.split(":", 1)[1].strip().lower()
                for r in valid_ratings:
                    if r in val:
                        governance = r
                        break
            elif line.upper().startswith("OVERALL:"):
                val = line.split(":", 1)[1].strip().lower()
                for r in valid_ratings:
                    if r in val:
                        overall = r
                        break
            elif line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip()

        self.environmental = environmental
        self.social = social
        self.governance = governance
        self.overall = overall
        self.summary = summary
        self.has_evaluated = True
        return self.overall
