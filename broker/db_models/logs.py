from src import db


class Log(db.Model):
    __tablename__ = "log"
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(
        db.String(256),
        db.ForeignKey("topic.name"),
        nullable=False,
        primary_key=True,
    )
    producer_id = db.Column(
        db.String(32),nullable=False
    )
    message = db.Column(db.String(256), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    __table_args__ = tuple(
        db.UniqueConstraint("id", "topic_name", name="log_id_constraint")
    )