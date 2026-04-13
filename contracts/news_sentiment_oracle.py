
# { “Depends”: “py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6” }

from genlayer import *
import typing

class NewsSentimentOracle(gl.Contract):
topic: str
sentiment: str
has_analyzed: bool

```
def __init__(self, topic: str):
    self.topic = topic
    self.sentiment = ""
    self.has_analyzed = False

@gl.public.view
def get_sentiment(self) -> str:
    return self.sentiment

@gl.public.view
def get_topic(self) -> str:
    return self.topic

@gl.public.view
def is_analyzed(self) -> bool:
    return self.has_analyzed

@gl.public.write
def analyze(self) -> typing.Any:
    if self.has_analyzed:
        return "Already analyzed"

    topic = self.topic
    source_url = "https://news.google.com/search?q=" + topic + "&hl=en"

    def get_sentiment() -> str:
        response = gl.nondet.web.get(source_url)
        web_data = response.body.decode("utf-8")
        task = (
            "You are analyzing news headlines about the topic: " + topic + ".\n"
            "Based on the following web content, respond with exactly one word: "
            "positive, negative, or neutral.\n"
            "Web content:\n" + web_data[:2000]
        )
        result = gl.nondet.exec_prompt(task)
        if "positive" in result.lower():
            return "positive"
        elif "negative" in result.lower():
            return "negative"
        return "neutral"

    self.sentiment = gl.eq_principle.strict_eq(get_sentiment)
    self.has_analyzed = True
    return self.sentiment
```
