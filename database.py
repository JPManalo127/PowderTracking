from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(
    "sqlite:///powder_tracker.db")

Session = sessionmaker(bind=engine)

Base = declarative_base()


class Dispenser(Base):
    __tablename__ = "dispensers"

    id = Column(Integer, primary_key=True)
    dispenser_name = Column(String, unique=True, nullable=False)
    current_machine = Column(String)
    material = Column(String)
    status = Column(String, default="ACTIVE")
    kg_in_dispenser = Column(Float)
    feed_direction = Column(String)
    notes = Column(String)

class Batch(Base):
    __tablename__ = "powder_batches"
    id = Column(Integer, primary_key=True)
    batch_number = Column(String, unique=True, nullable=False)
    grade = Column(String)
    condition = Column(String)
    kg = Column(Float)
    location = Column(String)
    status = Column(String, default="ACTIVE")

class DispenserLayer(Base):
    __tablename__ = "dispenser_layers"
    id = Column(Integer, primary_key=True)
    dispenser_id=Column(Integer, nullable=False)
    batch_number=Column(String, nullable=False)
    kg=Column(Float, nullable=False)
    position=Column(Integer, nullable=False)

class Build(Base):
    __tablename__ = "builds"
    id = Column(Integer, primary_key=True)
    build_number = Column(String, unique=True, nullable=False)
    build_date = Column(String)
    powder_used = Column(Float)
    recovery_batch = Column(String)
    recovery_weight = Column(Float)
    dispenser_name = Column(String)

class BuildConsumption(Base):
    __tablename__ = "build_consumption"
    id = Column(Integer, primary_key=True)
    build_number = Column(String)
    batch_number = Column(String)
    kg = Column(Float)

class BatchComponent(Base):
    __tablename__ = "batch_components"
    id = Column(Integer, primary_key=True)
    parent_batch = Column(String)
    component_batch = Column(String)
    kg = Column(Float)

def get_recovery_batch(session):

    batches = session.query(Batch).filter(
        Batch.batch_number.like("RB%")
    ).all()
    highest = 0
    for batch in batches:
        try:
            number = int(
                batch.batch_number.replace("RB", "")
            )
            highest = max(highest, number)
        except:
            pass
    return f"RB{highest + 1:04d}"
    
Base.metadata.create_all(engine)

