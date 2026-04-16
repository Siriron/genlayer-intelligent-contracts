
# { “Depends”: “py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6” }

from genlayer import *
import typing

class WeatherCropAdvisor(gl.Contract):
region: str
crop: str
advice: str
suitability: str
has_evaluated: bool

```
def __init__(self, region: str, crop: str):
    self.region = region
    self.crop = crop
    self.advice = ""
    self.suitability = ""
    self.has_evaluated = False

@gl.public.view
def get_region(self) -> str:
    return self.region

@gl.public.view
def get_crop(self) -> str:
    return self.crop

@gl.public.view
def get_advice(self) -> str:
    return self.advice

@gl.public.view
def get_suitability(self) -> str:
    return self.suitability

@gl.public.view
def is_evaluated(self) -> bool:
    return self.has_evaluated

@gl.public.write
def evaluate(self) -> typing.Any:
    if self.has_evaluated:
        return "Already evaluated"

    region = self.region
    crop = self.crop
    source_url = "https://wttr.in/" + region.replace(" ", "+") + "?format=j1"

    def get_evaluation() -> str:
        response = gl.nondet.web.get(source_url)
        web_data = response.body.decode("utf-8")
        task = (
            "You are an agricultural advisor.\n"
            "Region: " + region + "\n"
            "Crop: " + crop + "\n"
            "Weather data (JSON):\n" + web_data[:2000] + "\n\n"
            "Based on current weather conditions, is this region currently suitable for growing this crop?\n"
            "Respond in this exact format:\n"
            "SUITABILITY: suitable OR unsuitable OR marginal\n"
            "ADVICE: one sentence of practical farming advice for this crop in this region right now."
        )
        result = gl.nondet.exec_prompt(task)
        return result

    raw = gl.eq_principle.strict_eq(get_evaluation)

    suitability = "unknown"
    advice = raw
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("SUITABILITY:"):
            val = line.split(":", 1)[1].strip().lower()
            if "unsuitable" in val:
                suitability = "unsuitable"
            elif "marginal" in val:
                suitability = "marginal"
            elif "suitable" in val:
                suitability = "suitable"
        elif line.upper().startswith("ADVICE:"):
            advice = line.split(":", 1)[1].strip()

    self.suitability = suitability
    self.advice = advice
    self.has_evaluated = True
    return self.suitability
```
