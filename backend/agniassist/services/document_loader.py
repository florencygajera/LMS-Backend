import os
import sys

# Must add backend to path to import correctly
sys.path.insert(0, os.path.dirname(__file__) + r"\..\..")

from agniassist.services.rag_service import rag_service

def load_documents():
    count = 0
    docs = {
        "training": [
            "Physical training is mandatory for all Agniveer personnel. Daily schedule includes: Running (5km), Push-ups (50), Pull-ups (10), Sit-ups (50), and Marching (2km). Performance is monitored weekly. Minimum fitness standards: 1.6km run in 7 minutes, 20 push-ups, 8 pull-ups.",
            "Weapons training includes: Rifle (INSAS), LMG, Grenade throwing, and Field tactics. Safety protocols must be followed at all times. Minimum qualifying score: 35/50 in marksmanship test."
        ],
        "medical": [
            "Medical fitness is critical for active duty. Regular health checkups mandatory every 6 months. BMI must be between 18.5-25. Vision standards: 6/6 in both eyes. Height requirement: 170cm minimum."
        ],
        "recruitment": [
            "All personnel must maintain discipline. Duty hours: 0600-2000. Leave requests must be submitted 48 hours in advance. Annual leave: 30 days. Sick leave: 15 days."
        ]
    }
    
    for category, texts in docs.items():
        for text in texts:
            rag_service.integrate_document(f"[{category.upper()}] " + text)
            count += 1
            print(f"Indexed document for category {category}")

if __name__ == "__main__":
    load_documents()
    print(f"Total FAISS Index Documents: {rag_service.index.ntotal}")
