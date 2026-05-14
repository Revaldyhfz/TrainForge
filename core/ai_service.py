import json
from django.conf import settings
from openai import OpenAI

# ref: OpenAI Python SDK — https://github.com/openai/openai-python


SYSTEM_PROMPT = """You are an expert personal training assistant helping a certified trainer design exercise plans for their client.

Your job: propose a list of exercises tailored to the client's goals, past progress, and the trainer's specifications. The trainer reviews and edits your suggestions before saving — you are an assistant, not the decision-maker.

Always respond as JSON with this exact shape:
{
  "message": "A short conversational message explaining your reasoning (2-3 sentences). Reference specific details from the client's context when relevant.",
  "exercises": [
    {
      "name": "Exercise name",
      "description": "1-2 sentence form cue or note",
      "exercise_type": "reps|duration|distance",
      "sets": 3,
      "reps": 10,
      "duration_minutes": null,
      "distance_km": null
    }
  ]
}

Rules:
- Propose 4-8 exercises per plan
- Exercise names must be specific (e.g., "Barbell Back Squat" not just "Squat")
- Match the trainer's equipment preference
- Respect session duration: roughly 5 minutes per exercise including rest
- If the client has past progress logs, mention the progression in your message
- Never recommend exercises that could be dangerous without a trainer present

EXERCISE TYPE SELECTION — choose carefully:

REPS-based (exercise_type="reps"): Strength training where the goal is performing a specific number of repetitions per set. Use when the exercise has a clear "rep" — bench press, squat, pull-up, dumbbell row, plank-to-pushup, etc.
  → Fill: sets (integer), reps (integer)
  → Set to null: duration_minutes, distance_km

DURATION-based (exercise_type="duration"): Time-based holds or interval work where the goal is sustaining effort for X minutes per set. Use for: plank holds, wall sits, HIIT rounds, jumping rope sessions.
  → ALSO use for indoor cardio machines (treadmill, stationary bike, elliptical, rowing machine) UNLESS the trainer's goal explicitly mentions a target distance.
  → Fill: sets (integer), duration_minutes (integer)
  → Set to null: reps, distance_km

DISTANCE-based (exercise_type="distance"): Cardio with a distance goal. Use when the trainer's goal mentions kilometres, miles, a race distance (5K, half-marathon), or "running X km".
  → Examples: "Improve 5K time" → distance. "10km Sunday run" → distance.
  → Fill: distance_km (number, can be decimal like 5.5)
  → Set to null: sets, reps, duration_minutes

CRITICAL: If you choose "distance", the distance_km field MUST contain a number. Never output "distance" type with distance_km as null.
CRITICAL: If you choose "duration", duration_minutes MUST contain a number. Never output "duration" type with duration_minutes as null.

- Output ONLY the JSON object, no markdown fences, no extra text"""


def build_user_message(plan, questionnaire, client_obj, progress_summary, refinement_feedback=None):
    profile_lines = []
    if client_obj.age:
        profile_lines.append(f"Age: {client_obj.age}")
    if client_obj.height_cm:
        profile_lines.append(f"Height: {client_obj.height_cm} cm")
    if client_obj.weight_kg:
        profile_lines.append(f"Weight: {client_obj.weight_kg} kg")
    if client_obj.fitness_level:
        profile_lines.append(f"Fitness level: {client_obj.get_fitness_level_display()}")
    profile_block = "\n".join(profile_lines) if profile_lines else "Not provided"

    parts = [
        f"Plan title: {plan.title}",
        f"Plan description: {plan.description or 'None provided'}",
        f"Client name: {client_obj.name}",
        f"Client profile:\n{profile_block}",
        f"Client goals: {client_obj.goals or 'None recorded'}",
        f"Past progress summary: {progress_summary or 'No prior progress logged'}",
        "",
        "Trainer specifications:",
        f"- Target muscle groups: {questionnaire['muscle_groups']}",
        f"- Session duration: {questionnaire['session_duration']} minutes",
        f"- Goal: {questionnaire['goal']}",
        f"- Target date: {questionnaire['target_date']}",
        f"- Equipment preference: {questionnaire['equipment']}",
    ]

    if refinement_feedback:
        parts.append("")
        parts.append(f"Trainer feedback on previous suggestion: {refinement_feedback}")
        parts.append("Please revise your exercise list accordingly.")

    return "\n".join(parts)


def generate_exercises(plan, questionnaire, client_obj, progress_summary, conversation_history=None, refinement_feedback=None):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    user_message = build_user_message(
        plan=plan,
        questionnaire=questionnaire,
        client_obj=client_obj,
        progress_summary=progress_summary,
        refinement_feedback=refinement_feedback,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=messages,
        max_completion_tokens=2000,
        response_format={"type": "json_object"},
    )

    raw_text = response.choices[0].message.content.strip()
    parsed = json.loads(raw_text)

    return {
        "message": parsed.get("message", ""),
        "exercises": parsed.get("exercises", []),
        "assistant_response": raw_text,
    }


def build_progress_summary(client_obj):
    from .models import ProgressLog
    logs = ProgressLog.objects.filter(client=client_obj).select_related('exercise').order_by('-logged_at')[:20]
    if not logs:
        return ""

    lines = []
    for log in logs:
        lines.append(
            f"{log.logged_at.strftime('%Y-%m-%d')}: {log.exercise.name} — {log.summary()}"
        )
    return "\n".join(lines)