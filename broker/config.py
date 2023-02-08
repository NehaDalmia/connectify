class Config:
    """Base config."""


class ProdConfig(Config):
    FLASK_ENV = "production"
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres:postgres@masterdb-1:5432/masterdb-1"
    )
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    FLASK_ENV = "development"
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres:postgres@masterdb-1:5432/masterdb-1"
    )
    DEBUG = True
    TESTING = True