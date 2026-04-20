# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import typing


class LaborMarketStressMonitor(gl.Contract):
    sector: str
    stress_level: str
    trend: str
    summary: str
    key_driver: str
    has_analyzed: bool

    def __init__(self, sector: str):
        self.sector = sector
        self.stress_level = ""
        self.trend = ""
        self.summary = ""
        self.key_driver = ""
        self.has_analyzed = False

    @gl.public.view
    def get_sector(self) -> str:
        return self.sector

    @gl.public.view
    def get_stress_level(self) -> str:
        return self.stress_level

    @gl.public.view
    def get_trend(self) -> str:
        return self.trend

    @gl.public.view
    def get_summary(self) -> str:
        return self.summary

    @gl.public.view
    def get_key_driver(self) -> str:
        return self.key_driver

    @gl.public.view
    def is_analyzed(self) -> bool:
        return self.has_analyzed

    @gl.public.write
    def analyze(self) -> typing.Any:
        if self.has_analyzed:
            return "Already analyzed"

        sector = self.sector
        source_url = (
            "https://news.google.com/rss/search?q="
            + sector.replace(" ", "+")
            + "+labor+market+jobs+employment+layoffs&hl=en-US&gl=US&ceid=US:en"
        )

        def get_analysis() -> str:
            response = gl.nondet.web.get(source_url)
            web_data = response.body.decode("utf-8")
            task = (
                "You are a professional labor market analyst.\n"
                "Sector: " + sector + "\n"
                "Live news feed:\n" + web_data[:2000] + "\n\n"
                "Based on this data, assess the current labor market conditions for this sector.\n"
                "Respond in this exact format:\n"
                "STRESS_LEVEL: stable OR moderate OR stressed OR critical\n"
                "TREND: hiring OR neutral OR layoffs\n"
                "SUMMARY: one sentence describing current labor market conditions\n"
                "KEY_DRIVER: one sentence identifying the main factor driving current conditions"
            )
            result = gl.nondet.exec_prompt(task)
            return result

        raw = gl.eq_principle.strict_eq(get_analysis)

        stress_level = "unknown"
        trend = "unknown"
        summary = ""
        key_driver = ""

        for line in raw.splitlines():
            line = line.strip()
            if line.upper().startswith("STRESS_LEVEL:"):
                val = line.split(":", 1)[1].strip().lower()
                if "critical" in val:
                    stress_level = "critical"
                elif "stressed" in val:
                    stress_level = "stressed"
                elif "moderate" in val:
                    stress_level = "moderate"
                elif "stable" in val:
                    stress_level = "stable"
            elif line.upper().startswith("TREND:"):
                val = line.split(":", 1)[1].strip().lower()
                if "layoffs" in val:
                    trend = "layoffs"
                elif "hiring" in val:
                    trend = "hiring"
                elif "neutral" in val:
                    trend = "neutral"
            elif line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip()
            elif line.upper().startswith("KEY_DRIVER:"):
                key_driver = line.split(":", 1)[1].strip()

        self.stress_level = stress_level
        self.trend = trend
        self.summary = summary
        self.key_driver = key_driver
        self.has_analyzed = True
        return self.stress_level
