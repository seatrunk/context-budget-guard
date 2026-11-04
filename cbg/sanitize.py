"""Neutraliza delimitadores do wrapper de confiança (issue #8)."""
import re

WRAPPER = "untrusted_tool_result"
OPEN = "<" + WRAPPER + ">"
CLOSE = "</" + WRAPPER + ">"
# Qualquer variação de caixa/espaço de <untrusted_tool_result ...> ou </ untrusted_tool_result>.
_DELIM = re.compile(r"<(\s*/?\s*)(untrusted_tool_result)", re.IGNORECASE)


def neutralize(text: str) -> str:
    """Troca o '<' de cada delimitador literal por '&lt;'.

    Determinístico e idempotente; o texto continua legível e nunca casa com OPEN/CLOSE.
    """
    return _DELIM.sub(lambda m: "&lt;" + m.group(1) + m.group(2), text)


def count_delimiters(text: str) -> int:
    return len(_DELIM.findall(text))


def neutralize_body(text: str) -> str:
    """Corpo não confiável: além dos delimitadores, impede forjar tags de nota/recibo do cbg."""
    text = neutralize(text)
    return re.sub(r"\[(note:|cbg)", lambda m: "[untrusted-" + m.group(1), text)
