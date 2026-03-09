from core.analysis_engine import AnalysisEngine
from models.psychological_state import PsychologicalState

analysis_engine = AnalysisEngine()
psy_state = PsychologicalState()

while True:

    user_input = input("Usuario: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    result = analysis_engine.analyze(user_input)

    psy_state.register_analysis(result)

    print("\nAnálisis:", result)
    print("Tendencia:", psy_state.get_trend())
    print()