from ..utils import db
from datetime import datetime, timezone

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    email =  db.Column( db.String(20) , nullable=False , unique=True )
    full_name = db.Column(db.String(50), nullable=False )
    date_of_birth =  db.Column(db.String(50), nullable=False )
    created_at = db.Column(db.DateTime() , nullable=False , default=datetime.now(timezone.utc))
    full_name = db.Column(db.String(10), nullable=False )
    courses = db.relationship('Course', secondary='student_course')
    score = db.relationship('Score', backref='student_score', lazy=True)


    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()


    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)


    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def __repr__(self) -> str:
        return self.email