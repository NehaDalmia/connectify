from src import db


class Producer(db.Model):
    __tablename__ = "producer"
    id = db.Column(db.String(32), primary_key=True, index=True)
    topic_name = db.Column(
        db.String(256),  nullable=False
    )
    partition_index = db.Column(db.Integer)
    ___table_args__ = (db.ForeignKeyConstraint([topic_name, partition_index],
                                           ["topic.name", "topic.partition_index"]), {})