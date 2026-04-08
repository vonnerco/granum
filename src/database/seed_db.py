from __future__ import annotations

import asyncio

from sqlalchemy import delete

from src.database.connection import DatabaseManager
from src.database.models import Interaction

SAMPLE_ROWS = [
    Interaction(
        input_text='arrived on site lawn was a mess weeds everywhere did full mow edging and cleanup customer seemed happy will need to come back for fertilizer app next week',
        enhanced_text='Work completed:\n- Full mow\n- Edging\n- Debris cleanup\n\nOutcome/Follow-up:\n- Customer seemed happy\n- Fertilizer application scheduled for next week',
        model_used='gemini-2.5-flash-lite',
        prompt_tokens=145,
        completion_tokens=71,
        latency_ms=612,
        status='success',
        error_message=None,
    ),
    Interaction(
        input_text='trimmed hedges in front yard, removed clippings, advised irrigation tune-up',
        enhanced_text='Work completed:\n- Trimmed front-yard hedges\n- Removed clippings\n\nOutcome/Follow-up:\n- Recommended irrigation tune-up',
        model_used='gemini-2.5-flash-lite',
        prompt_tokens=88,
        completion_tokens=49,
        latency_ms=430,
        status='success',
        error_message=None,
    ),
    Interaction(
        input_text='sprinkler zone 2 not turning on replaced solenoid tested all zones',
        enhanced_text='Work completed:\n- Diagnosed Zone 2 activation issue\n- Replaced faulty solenoid\n- Tested all sprinkler zones\n\nOutcome/Follow-up:\n- System operational at departure',
        model_used='gemini-2.5-flash-lite',
        prompt_tokens=96,
        completion_tokens=56,
        latency_ms=487,
        status='success',
        error_message=None,
    ),
    Interaction(
        input_text='customer requested emergency cleanup after storm',
        enhanced_text=None,
        model_used='llm_unavailable',
        prompt_tokens=0,
        completion_tokens=0,
        latency_ms=901,
        status='failure',
        error_message='LLM provider timeout during content generation.',
    ),
    Interaction(
        input_text='{"txt":"missing expected field"}',
        enhanced_text=None,
        model_used='validation',
        prompt_tokens=0,
        completion_tokens=0,
        latency_ms=0,
        status='failure',
        error_message='Validation failed: missing required field "text".',
    ),
]


async def main() -> None:
    db = DatabaseManager('sqlite+aiosqlite:///data/text_enhancer.db')
    await db.init_models()

    async with db.session_factory() as session:
        await session.execute(delete(Interaction))
        session.add_all(SAMPLE_ROWS)
        await session.commit()

    await db.close()


if __name__ == '__main__':
    asyncio.run(main())
