import asyncio

from sqlalchemy import select

from src.core.enhancer_service import EnhancementError, EnhancerService
from src.database.connection import DatabaseManager
from src.database.models import Interaction


class SuccessLLMClient:
    def enhance(self, raw_text: str):
        return type(
            'LLMResult',
            (),
            {
                'enhanced_text': f'Work completed:\n- {raw_text}\n\nOutcome/Follow-up:\n- complete',
                'model_used': 'mock-success-model',
                'prompt_tokens': 11,
                'completion_tokens': 9,
            },
        )()


class FailureLLMClient:
    def enhance(self, raw_text: str):
        raise RuntimeError('simulated provider timeout')


def test_service_logs_success(tmp_path):
    async def run():
        db_path = tmp_path / 'service_success.db'
        db = DatabaseManager(f'sqlite+aiosqlite:///{db_path.as_posix()}')
        await db.init_models()

        service = EnhancerService(db.session_factory, SuccessLLMClient())
        result = await service.enhance_text('trimmed hedges and removed weeds')

        assert result.model_used == 'mock-success-model'
        assert result.token_usage.prompt_tokens == 11

        async with db.session_factory() as session:
            rows = (await session.execute(select(Interaction))).scalars().all()
            assert len(rows) == 1
            assert rows[0].status == 'success'

        await db.close()

    asyncio.run(run())


def test_service_logs_failure(tmp_path):
    async def run():
        db_path = tmp_path / 'service_failure.db'
        db = DatabaseManager(f'sqlite+aiosqlite:///{db_path.as_posix()}')
        await db.init_models()

        service = EnhancerService(db.session_factory, FailureLLMClient())

        try:
            await service.enhance_text('sprinkler valve issue')
            raise AssertionError('Expected EnhancementError was not raised')
        except EnhancementError:
            pass

        async with db.session_factory() as session:
            rows = (await session.execute(select(Interaction))).scalars().all()
            assert len(rows) == 1
            assert rows[0].status == 'failure'
            assert 'simulated provider timeout' in (rows[0].error_message or '')

        await db.close()

    asyncio.run(run())
