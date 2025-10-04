import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.container import Container
from src.routes import routers_class
from src.utils.exception_handlers import validation_exception_handler
from src.utils.lifespan_events import shutdown, startup
from src.utils.settings import Settings

settings = Settings()


async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()


def register_routers(app: FastAPI, container):
    for router_class in routers_class:
        router_instance = router_class(container)
        app.include_router(router_instance.router)


def create_app(database_url=settings.DATABASE_URL) -> FastAPI:
    app = FastAPI(
        title='Meu App',
        description='Documentação da API',
        version='1.0.0',
        lifespan=lifespan,
    )
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*'],
        allow_credentials=True,
    )

    container = Container()
    container.config.DATABASE_URL.from_value(database_url)

    register_routers(app, container)

    return app, container


app, container = create_app()


@app.get('/', include_in_schema=False)
async def main_route():
    return RedirectResponse(url='/docs')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
