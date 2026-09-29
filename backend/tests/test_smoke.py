def test_import():
    from app.main import app
    from app.core.config import settings
    assert app.title == settings.APP_NAME
