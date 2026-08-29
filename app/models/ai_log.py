import datetime
from app import db

class AILog(db.Model):
    __tablename__ = 'ai_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query_text = db.Column(db.Text, nullable=False)
    intent_extracted = db.Column(db.String(100), nullable=True)
    category_matched = db.Column(db.String(100), nullable=True)
    results_count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref='ai_logs', lazy=True)

    def __repr__(self):
        return f'<AILog intent={self.intent_extracted} cat={self.category_matched}>'
