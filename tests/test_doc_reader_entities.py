import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.documents.doc_reader import DocReader


def make_reader():
    return DocReader()


def test_extracts_actual_date_value():
    reader = make_reader()
    entities = reader._extract_entities("Próxima cita el 14/03/2026 en la mañana.")

    assert "14/03/2026" in entities


def test_extracts_doctor_name_not_just_the_word_doctor():
    reader = make_reader()
    entities = reader._extract_entities("Atendido por Dr. Carlos Ramirez el día de hoy.")

    assert "Dr. Carlos Ramirez" in entities


def test_extracts_hospital_name():
    reader = make_reader()
    entities = reader._extract_entities("Referido al Hospital San Vicente para estudios.")

    assert "Hospital San Vicente" in entities


def test_extracts_medication_with_dosage():
    reader = make_reader()
    entities = reader._extract_entities("Tomar Paracetamol 500mg cada 8 horas.")

    assert "Paracetamol 500mg" in entities


def test_falls_back_to_generic_keyword_when_no_structured_match():
    reader = make_reader()
    entities = reader._extract_entities("El paciente refiere dolor y se indica tratamiento.")

    assert "tratamiento" in entities


def test_no_entities_on_unrelated_text():
    reader = make_reader()
    entities = reader._extract_entities("El clima hoy está soleado y agradable.")

    assert entities == []
