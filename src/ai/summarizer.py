import os
from typing import Any

from dotenv import load_dotenv
from google import genai


load_dotenv()


SYSTEM_INSTRUCTION = """
You are a data analytics assistant for a public transport
reliability system.

Your job is to explain the worst-performing route using ONLY
the structured evidence provided by the data pipeline.

Rules:
1. Do not invent facts.
2. Do not calculate new metrics.
3. Do not change any numbers.
4. Mention the route name and route ID.
5. Explain why it performed poorly using the supplied evidence.
6. Keep the answer concise and professional.
7. If the evidence is insufficient, explicitly say so.
"""


def build_prompt(evidence: dict[str, Any]) -> str:
    """
    Build a grounded prompt from SQL-generated evidence.
    """

    return f"""
Analyze the following route reliability evidence.

Route ID: {evidence["route_id"]}
Route Name: {evidence["route_name"]}
Origin: {evidence["origin"]}
Destination: {evidence["destination"]}

Total trips: {evidence["total_trips"]}
Completed trips: {evidence["completed_trips"]}
Cancelled trips: {evidence["cancelled_trips"]}
On-time trips: {evidence["on_time_trips"]}
Delayed trips: {evidence["delayed_trips"]}

Average delay: {evidence["avg_delay_minutes"]} minutes
Maximum delay: {evidence["max_delay_minutes"]} minutes
On-time rate: {evidence["on_time_rate"]}%
Cancellation rate: {evidence["cancellation_rate"]}%
Reliability score: {evidence["reliability_score"]}

Write a short explanation of why this route is the
worst-performing route.
"""


def generate_summary(evidence: dict[str, Any]) -> str:
    """
    Generate an AI summary from structured SQL evidence.
    """

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("AI_MODEL", "gemini-3.8-flash")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from the environment."
        )

    client = genai.Client(api_key=api_key)

    prompt = build_prompt(evidence)

    interaction = client.interactions.create(
        model=model,
        system_instruction=SYSTEM_INSTRUCTION,
        input=prompt,
        generation_config={
            "temperature": 0.2,
            "thinking_level": "low",
        },
    )

    summary = interaction.output_text

    if not summary:
        raise RuntimeError(
            "AI returned an empty response."
        )

    return summary