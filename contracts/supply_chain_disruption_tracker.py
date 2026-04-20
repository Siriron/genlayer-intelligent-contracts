# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import typing


class SupplyChainDisruptionTracker(gl.Contract):
    industry: str
    severity: str
    affected_regions: str
    recommendation: str
    summary: str
    has_analyzed: bool

    def __init__(self, industry: str):
        self.industry = industry
        self.severity = ""
        self.affected_regions = ""
        self.recommendation = ""
        self.summary = ""
        self.has_analyzed = False

    @gl.public.view
    def get_industry(self) -> str:
        return self.industry

    @gl.public.view
    def get_severity(self) -> str:
        return self.severity

    @gl.public.view
    def get_affected_regions(self) -> str:
        return self.affected_regions

    @gl.public.view
    def get_recommendation(self) -> str:
        return self.recommendation

    @gl.public.view
    def get_summary(self) -> str:
        return self.summary

    @gl.public.view
    def is_analyzed(self) -> bool:
        return self.has_analyzed

    @gl.public.write
    def analyze(self) -> typing.Any:
        if self.has_analyzed:
            return "Already analyzed"

        industry = self.industry
        source_url = (
            "https://news.google.com/rss/search?q="
            + industry.replace(" ", "+")
            + "+supply+chain+disruption&hl=en-US&gl=US&ceid=US:en"
        )

        def get_analysis() -> str:
            response = gl.nondet.web.get(source_url)
            web_data = response.body.decode("utf-8")
            task = (
                "You are a professional supply chain analyst.\n"
                "Industry: " + industry + "\n"
                "Live news feed:\n" + web_data[:2000] + "\n\n"
                "Based on this data, assess the current supply chain disruption status for this industry.\n"
                "Respond in this exact format:\n"
                "SEVERITY: low OR medium OR high OR critical\n"
                "AFFECTED_REGIONS: comma-separated list of affected regions, or none identified\n"
                "SUMMARY: one sentence describing the main disruption\n"
                "RECOMMENDATION: one actionable sentence for businesses operating in this industry"
            )
            result = gl.nondet.exec_prompt(task)
            return result

        raw = gl.eq_principle.strict_eq(get_analysis)

        severity = "unknown"
        affected_regions = ""
        summary = ""
        recommendation = ""

        for line in raw.splitlines():
            line = line.strip()
            if line.upper().startswith("SEVERITY:"):
                val = line.split(":", 1)[1].strip().lower()
                if "critical" in val:
                    severity = "critical"
                elif "high" in val:
                    severity = "high"
                elif "medium" in val:
                    severity = "medium"
                elif "low" in val:
                    severity = "low"
            elif line.upper().startswith("AFFECTED_REGIONS:"):
                affected_regions = line.split(":", 1)[1].strip()
            elif line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip()
            elif line.upper().startswith("RECOMMENDATION:"):
                recommendation = line.split(":", 1)[1].strip()

        self.severity = severity
        self.affected_regions = affected_regions
        self.summary = summary
        self.recommendation = recommendation
        self.has_analyzed = True
        return self.severity
