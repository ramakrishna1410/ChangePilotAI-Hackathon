"""Requirement Agent (§4): summarizes and structures the raw change request
text into objective/scope/constraints/acceptance criteria (§3.1)."""
from app.agents.llm import call_structured
from app.models import RequirementSummary

SYSTEM_PROMPT = """You are the Requirement Agent inside ChangePilot AI, an enterprise
change-impact-analysis assistant. Extract a structured requirement summary from the raw
change request text below. Do not invent details that are not stated or reasonably
implied. Respond ONLY with a JSON object matching this shape:
{
  "objective": string,
  "scope": string,
  "constraints": string[],
  "acceptance_criteria": string[],
  "affected_application": string
}"""


def run(application: str, summary: str, description: str) -> RequirementSummary:
    user_prompt = (
        f"Application: {application}\n"
        f"Change request summary: {summary}\n"
        f"Change request description:\n{description}"
    )
    data = call_structured(SYSTEM_PROMPT, user_prompt)
    data.setdefault("affected_application", application)
    return RequirementSummary.model_validate(data)
