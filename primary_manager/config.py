class Config:
    """Base config."""


class ProdConfig(Config):
    FLASK_ENV = "production"
    # SQLALCHEMY_DATABASE_URI = (
    #     "postgresql://postgres:postgres@localhost:5432/test"
    # )
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    FLASK_ENV = "development"
    # SQLALCHEMY_DATABASE_URI = (
    #     "postgresql://postgres:postgres@localhost:5432/test"
    # )
    DEBUG = True
    TESTING = True