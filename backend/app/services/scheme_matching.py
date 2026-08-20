import operator
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Scheme
from app.repositories.entity_repositories import SchemeRepository

_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}


@dataclass
class ConditionResult:
    field: str
    operator: str
    value: object
    matched: bool
    description: str


@dataclass
class SchemeMatchResult:
    scheme_id: str
    scheme_name: str
    matched_conditions: list[str] = field(default_factory=list)
    missing_conditions: list[str] = field(default_factory=list)
    required_documents: list[str] = field(default_factory=list)
    official_source: str | None = None
    explanation: str = ""
    is_potentially_eligible: bool = False


def _describe(field_name: str, op: str, value) -> str:
    return f"{field_name} {op} {value}"


def _evaluate_condition(profile: dict, condition: dict) -> ConditionResult:
    field_name = condition["field"]
    op = condition["operator"]
    expected = condition["value"]
    actual = profile.get(field_name)

    fn = _OPERATORS.get(op)
    matched = False
    if fn is not None and actual is not None:
        try:
            matched = bool(fn(actual, expected))
        except TypeError:
            matched = False

    return ConditionResult(
        field=field_name, operator=op, value=expected, matched=matched, description=_describe(field_name, op, expected)
    )


def _evaluate_rules(profile: dict, rules: dict) -> tuple[list[ConditionResult], bool]:
    """rules shape: {"all": [condition, ...], "any": [condition, ...]}.
    Both keys optional; an empty ruleset matches nobody (never a scheme
    presented as eligible with zero real conditions)."""
    all_conditions = [_evaluate_condition(profile, c) for c in rules.get("all", [])]
    any_conditions = [_evaluate_condition(profile, c) for c in rules.get("any", [])]

    if not all_conditions and not any_conditions:
        return [], False

    all_pass = all(c.matched for c in all_conditions) if all_conditions else True
    any_pass = any(c.matched for c in any_conditions) if any_conditions else True
    overall = all_pass and any_pass
    return all_conditions + any_conditions, overall


async def match_schemes(db: AsyncSession, profile: dict) -> list[SchemeMatchResult]:
    """Citizen profile -> JSONB-defined rule engine -> matched schemes.
    Language is always 'appears potentially eligible', never a certainty
    claim — eligibility rules in government schemes have exceptions this
    engine cannot see."""
    schemes: list[Scheme] = await SchemeRepository(db).list_active()

    results: list[SchemeMatchResult] = []
    for scheme in schemes:
        conditions, overall = _evaluate_rules(profile, scheme.eligibility_rules or {})
        matched = [c.description for c in conditions if c.matched]
        missing = [c.description for c in conditions if not c.matched]

        if overall:
            explanation = (
                f"Based on the information provided, you appear potentially eligible for "
                f"'{scheme.name}'. This is not a final determination — verify with the "
                f"official source and required documents."
            )
        else:
            explanation = (
                f"Based on the information provided, you do not currently appear to meet "
                f"the conditions for '{scheme.name}'."
            )

        results.append(
            SchemeMatchResult(
                scheme_id=str(scheme.id),
                scheme_name=scheme.name,
                matched_conditions=matched,
                missing_conditions=missing,
                required_documents=scheme.required_documents or [],
                official_source=scheme.official_source,
                explanation=explanation,
                is_potentially_eligible=overall,
            )
        )

    results.sort(key=lambda r: r.is_potentially_eligible, reverse=True)
    return results
