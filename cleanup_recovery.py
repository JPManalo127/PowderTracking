from database import Session, Batch, BatchComponent

session = Session()

session.query(BatchComponent).filter(
    BatchComponent.parent_batch.like("RB%")
).delete(
    synchronize_session=False
)

session.query(Batch).filter(
    Batch.batch_number.like("RB%")
).delete(
    synchronize_session=False
)

session.commit()

print("Recovery batches removed.")
print("Batch component records removed.")
