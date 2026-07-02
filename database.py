from sqlalchemy import create_engine, Column, Integer,String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime , timezone

DATABASE_URL = "postgresql://fastapi:fastapi@fastapi-db:5432/fastapidb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class PendingReview(Base):
    __tablename__ = "pending_review"
    id = Column(Integer, primary_key = True, index= True)
    incoming_name = Column(String)
    incoming_dob = Column(String)
    matched_patient_id = Column(String)
    name_score = Column(Float)
    dob_match = Column(Integer)
    confidence = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(bind=engine)