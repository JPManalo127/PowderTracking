import pandas as pd
import numpy as np

from database import Session
from database import (
    Dispenser,
    Batch,
    DispenserLayer,
    Build,
    BuildConsumption,
    BatchComponent,
    MonthlyBalance,
    PowderTransaction,
    Sieve,
    SieveRun,
)

TABLES = [
    ("dispensers.csv", Dispenser),
    ("powder_batches.csv", Batch),
    ("dispenser_layers.csv", DispenserLayer),
    ("builds.csv", Build),
    ("build_consumption.csv", BuildConsumption),
    ("batch_components.csv", BatchComponent),
    ("monthly_balances.csv", MonthlyBalance),
    ("powder_transaction.csv", PowderTransaction),
    ("sieves.csv", Sieve),
    ("sieve_run.csv", SieveRun),
]

session = Session()

for filename, model in TABLES:

    print(f"\nImporting {filename}")

    df = pd.read_csv(filename)

    # Replace NaN with None for SQLAlchemy
    df = df.replace({np.nan: None})

    count = 0

    for row in df.to_dict(orient="records"):

        try:
            record = model(**row)
            session.add(record)
            count += 1

        except Exception as e:
            print(f"Error in {filename}: {e}")
            print(row)

    session.commit()

    print(f"Imported {count} records")

session.close()

print("\nMigration Complete")
