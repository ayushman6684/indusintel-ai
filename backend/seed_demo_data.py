"""
Loads 5 realistic industrial demo products into the database so the app
works immediately without requiring the evaluator to upload a document
(Section 11 of the spec).

Run:
    python seed_demo_data.py
"""
import os
from app.database import SessionLocal, Base, engine
from app import models

Base.metadata.create_all(bind=engine)

DEMO_PRODUCTS = [
    {
        "name": "IndusFlow HCX-500 Centrifugal Pump",
        "product_code": "HCX-500",
        "manufacturer": "IndusFlow Industries",
        "category": "Industrial Pumps",
        "description": "Heavy-duty end-suction centrifugal pump for water and chemical transfer in industrial applications.",
        "quality_score": 91.0,
        "status": "completed",
    },
    {
        "name": "PressureSense PS-200 Industrial Pressure Sensor",
        "product_code": "PS-200",
        "manufacturer": "PressureSense Corp",
        "category": "Sensors",
        "description": "High-accuracy piezoresistive pressure sensor for industrial process monitoring.",
        "quality_score": 88.0,
        "status": "completed",
    },
    {
        "name": "TorqueMax EM-750 Three-Phase Electric Motor",
        "product_code": "EM-750",
        "manufacturer": "TorqueMax Motors",
        "category": "Motors",
        "description": "IE3 premium efficiency three-phase induction motor for continuous industrial duty.",
        "quality_score": 85.0,
        "status": "completed",
    },
    {
        "name": "FlowGuard CV-100 Control Valve",
        "product_code": "CV-100",
        "manufacturer": "FlowGuard Systems",
        "category": "Valves",
        "description": "Globe-style control valve with pneumatic actuator for precise flow regulation.",
        "quality_score": 79.0,
        "status": "completed",
    },
    {
        "name": "DuraBear RB-6205 Deep Groove Ball Bearing",
        "product_code": "RB-6205",
        "manufacturer": "DuraBear Industrial",
        "category": "Bearings",
        "description": "Sealed deep groove ball bearing for high-speed rotating machinery.",
        "quality_score": 93.0,
        "status": "completed",
    },
]


def run():
    db = SessionLocal()
    try:
        existing = db.query(models.Product).count()
        if existing > 0:
            print(f"Database already has {existing} products. Skipping seed.")
            return

        for p in DEMO_PRODUCTS:
            db.add(models.Product(**p))
        db.commit()
        print(f"Seeded {len(DEMO_PRODUCTS)} demo products.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
