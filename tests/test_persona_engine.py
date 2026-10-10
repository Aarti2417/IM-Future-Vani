"""
Unit and Integration Tests for IndiaMART VANI Persona Engine
"""
import pytest
import os
import json
import shutil
import tempfile

from src.persona_generator import PersonaGenerator, Persona
from src.signal_detector import SignalDetector, DetectedSignal
from src.persona_manager import PersonaManager, AdaptationEvent
from src.persona_memory import PersonaMemoryStore, SellerMemory
from src.sarvam_client import MockSarvamClient, select_voice, VOICE_CATALOG
from src.call_simulator import CallSimulator


# ── Fixtures ───────────────────────────────────────────────

@pytest.fixture
def sample_sellers():
    sellers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_sample", "sellers.json")
    with open(sellers_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_sarvam():
    return MockSarvamClient()


# ── Persona Generator Tests ───────────────────────────────

def test_persona_generator_frustrated_seller(sample_sellers):
    # Seller 0 has showed_frustration = 1
    frustrated_seller = sample_sellers[0]
    gen = PersonaGenerator()
    persona = gen.generate_persona(frustrated_seller)

    assert persona.seller_id == str(frustrated_seller["fk_glusr_usr_id"])
    assert persona.tone == "empathetic_problem_solver"
    assert persona.script_strategy == "problem_solving"
    assert persona.pace <= 0.92
    assert "empathy" in persona.rationale["tone"].lower() or "de-escalate" in persona.rationale["tone"].lower()
    assert len(persona.opening_line) > 10
    assert "IndiaMART" in persona.opening_line


def test_persona_generator_enterprise_seller(sample_sellers):
    # Seller 4 has 5 - 25 Cr turnover
    enterprise_seller = sample_sellers[4]
    gen = PersonaGenerator()
    persona = gen.generate_persona(enterprise_seller)

    assert persona.pace >= 1.0
    assert persona.formality == "formal_corporate"
    assert persona.tone in ["direct_closing", "consultative"]
    assert "roi_numbers" in persona.script_strategy


def test_persona_generator_sparse_seller():
    # Cold-start seller with minimal attributes
    sparse_seller = {
        "fk_glusr_usr_id": 999999999,
        "seller_state": "Delhi"
    }
    gen = PersonaGenerator()
    persona = gen.generate_persona(sparse_seller)

    assert persona.seller_id == "999999999"
    assert persona.language_mix in ["hinglish", "pure_hindi"]
    assert persona.formality == "respectful_warm"
    assert 0.85 <= persona.pace <= 1.15


# ── Signal Detector Tests ─────────────────────────────────

def test_signal_detector_rushed():
    detector = SignalDetector()
    sig = detector.detect("Jaldi bolo bhai, main driving kar raha hu, time nahi hai bilkul")
    assert sig.signal == "rushed"
    assert sig.confidence >= 0.70
    assert "jaldi" in sig.cues_matched or "driving" in sig.cues_matched or "time nahi" in sig.cues_matched


def test_signal_detector_confused():
    detector = SignalDetector()
    sig = detector.detect("Kya matlab? Kaun bol raha hai? Samajh nahi aaya kiska call hai")
    assert sig.signal == "confused"
    assert sig.confidence >= 0.70
    assert any(c in sig.cues_matched for c in ["kya matlab", "kaun bol raha", "samajh nahi aaya"])


def test_signal_detector_frustrated():
    detector = SignalDetector()
    sig = detector.detect("Bar bar call mat karo! Harassment band karo, nahi chahiye!")
    assert sig.signal == "frustrated"
    assert sig.confidence >= 0.80


def test_signal_detector_engaged():
    detector = SignalDetector()
    sig = detector.detect("Achha bataiye, leads kaise aati hain aur kitna kharcha padega?")
    assert sig.signal == "engaged"
    assert sig.confidence >= 0.70


def test_signal_detector_hesitant():
    detector = SignalDetector()
    sig = detector.detect("Pehle bhi liya tha, faayda nahi hua, costly lag raha hai sochna padega")
    assert sig.signal == "hesitant"
    assert sig.confidence >= 0.70


def test_signal_detector_interruption():
    detector = SignalDetector()
    sig = detector.detect("Sun sun sun...", acoustic_features={"interrupted": True})
    assert sig.signal == "interrupted"


# ── Persona Manager Tests ─────────────────────────────────

def test_persona_manager_adaptation_rushed(sample_sellers):
    gen = PersonaGenerator()
    persona = gen.generate_persona(sample_sellers[1])
    orig_pace = persona.pace

    manager = PersonaManager(persona)
    detector = SignalDetector()
    rushed_signal = detector.detect("Bolo jaldi mere paas time nahi hai")

    event = manager.adapt(rushed_signal, turn_number=2)
    assert event is not None
    assert manager.active_persona.pace > orig_pace
    assert event.signal_detected == "rushed"
    assert len(manager.trajectory) == 1


def test_persona_manager_adaptation_frustrated(sample_sellers):
    gen = PersonaGenerator()
    persona = gen.generate_persona(sample_sellers[1])

    manager = PersonaManager(persona)
    detector = SignalDetector()
    frustrated_signal = detector.detect("Bakwas mat karo bar bar phone karke!")

    event = manager.adapt(frustrated_signal, turn_number=2)
    assert event is not None
    assert manager.active_persona.tone == "empathetic_problem_solver"
    assert manager.active_persona.script_strategy == "problem_solving"
    assert "frustration" in event.adaptation_rationale.lower()


# ── Persona Memory Tests ──────────────────────────────────

def test_persona_memory_evolution(sample_sellers):
    temp_dir = tempfile.mkdtemp()
    temp_mem_file = os.path.join(temp_dir, "test_memory.json")

    try:
        store = PersonaMemoryStore(storage_path=temp_mem_file)
        gen = PersonaGenerator()
        seller = sample_sellers[1]
        sid = str(seller["fk_glusr_usr_id"])

        p_init = gen.generate_persona(seller)
        p_final = gen.generate_persona(seller)
        p_final.pace = 1.10
        p_final.tone = "direct_closing"

        # Record a successful call
        mem = store.record_call(
            seller_id=sid,
            disposition="meeting_fixed",
            initial_persona=p_init,
            final_persona=p_final,
            signals_encountered=["rushed", "engaged"],
            notes="Successful fast call"
        )

        assert mem.total_calls == 1
        assert mem.successful_calls == 1
        assert mem.preferred_pace == 1.10
        assert mem.preferred_tone == "direct_closing"

        # Now test that a new persona for this seller adopts the memory!
        p_new = gen.generate_persona(seller)
        p_evolved = store.apply_memory_to_persona(p_new)
        assert p_evolved.pace == 1.10
        assert p_evolved.tone == "direct_closing"
        assert "memory_evolution" in p_evolved.rationale

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ── End-to-End Simulation Tests ───────────────────────────

def test_call_simulator_full_flow(sample_sellers, mock_sarvam):
    temp_dir = tempfile.mkdtemp()
    temp_mem_file = os.path.join(temp_dir, "sim_test_memory.json")

    try:
        store = PersonaMemoryStore(storage_path=temp_mem_file)
        sim = CallSimulator(sarvam_client=mock_sarvam, memory_store=store)

        seller = sample_sellers[0]
        result = sim.run_simulation(seller, generate_audio=True)

        assert result.seller_id == str(seller["fk_glusr_usr_id"])
        assert result.total_turns >= 4
        assert len(result.trajectory) >= 1
        assert result.disposition != ""

        # Verify turns format
        for turn in result.turns:
            assert turn.speaker in ["bot", "seller"]
            assert len(turn.text) > 0
            if turn.speaker == "bot":
                assert turn.audio_base64 is not None

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
