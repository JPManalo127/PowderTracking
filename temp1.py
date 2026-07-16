from database import Session, Dispenser

session = Session()

for dispenser in session.query(Dispenser).all():
    print(
        dispenser.dispenser_name,
        dispenser.feed_direction
    )

session.close()
