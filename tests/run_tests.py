"""
Standard library test runner for IndiaMART VANI Persona Engine
Runs all test cases without requiring external pytest module.
"""
import unittest
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


class TestPersonaEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        sellers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_sample", "sellers.json")
        with open(sellers_path, "r", encoding="utf-8") as f:
            cls.sample_sellers = json.load(f)
        cls.mock_sarvam = MockSarvamClient()

    def test_persona_generator_frustrated_seller(self):
        frustrated_seller = self.sample_sellers[0]
        gen = PersonaGenerator()
        persona = gen.generate_persona(frustrated_seller)

        self.assertEqual(persona.seller_id, str(frustrated_seller["fk_glusr_usr_id"]))
        self.assertEqual(persona.tone, "empathetic_problem_solver")
        self.assertEqual(persona.script_strategy, "problem_solving")
        self.assertLessEqual(persona.pace, 0.92)
        self.assertTrue(
            "empathy" in persona.rationale["tone"].lower() or "de-escalate" in persona.rationale["tone"].lower()
        )
        self.assertGreater(len(persona.opening_line), 10)
        self.assertIn("IndiaMART", persona.opening_line)

    def test_persona_generator_enterprise_seller(self):
        enterprise_seller = self.sample_sellers[4]
        gen = PersonaGenerator()
        persona = gen.generate_persona(enterprise_seller)

        self.assertGreaterEqual(persona.pace, 1.0)
        self.assertEqual(persona.formality, "formal_corporate")
        self.assertIn(persona.tone, ["direct_closing", "consultative"])
        self.assertIn("roi_numbers", persona.script_strategy)

    def test_persona_generator_sparse_seller(self):
        sparse_seller = {
            "fk_glusr_usr_id": 999999999,
            "seller_state": "Delhi"
        }
        gen = PersonaGenerator()
        persona = gen.generate_persona(sparse_seller)

        self.assertEqual(persona.seller_id, "999999999")
        self.assertIn(persona.language_mix, ["hinglish", "pure_hindi"])
        self.assertEqual(persona.formality, "respectful_warm")
        self.assertTrue(0.85 <= persona.pace <= 1.15)

    def test_signal_detector_rushed(self):
        detector = SignalDetector()
        sig = detector.detect("Jaldi bolo bhai, main driving kar raha hu, time nahi hai bilkul")
        self.assertEqual(sig.signal, "rushed")
        self.assertGreaterEqual(sig.confidence, 0.70)
        self.assertTrue(
            "jaldi" in sig.cues_matched or "driving" in sig.cues_matched or "time nahi" in sig.cues_matched
        )

    def test_signal_detector_confused(self):
        detector = SignalDetector()
        sig = detector.detect("Kya matlab? Kaun bol raha hai? Samajh nahi aaya kiska call hai")
        self.assertEqual(sig.signal, "confused")
        self.assertGreaterEqual(sig.confidence, 0.70)
        self.assertTrue(any(c in sig.cues_matched for c in ["kya matlab", "kaun bol raha", "samajh nahi aaya"]))

    def test_signal_detector_frustrated(self):
        detector = SignalDetector()
        sig = detector.detect("Bar bar call mat karo! Harassment band karo, nahi chahiye!")
        self.assertEqual(sig.signal, "frustrated")
        self.assertGreaterEqual(sig.confidence, 0.80)

    def test_signal_detector_engaged(self):
        detector = SignalDetector()
        sig = detector.detect("Achha bataiye, leads kaise aati hain aur kitna kharcha padega?")
        self.assertEqual(sig.signal, "engaged")
        self.assertGreaterEqual(sig.confidence, 0.70)

    def test_signal_detector_hesitant(self):
        detector = SignalDetector()
        sig = detector.detect("Pehle bhi liya tha, faayda nahi hua, costly lag raha hai sochna padega")
        self.assertEqual(sig.signal, "hesitant")
        self.assertGreaterEqual(sig.confidence, 0.70)

    def test_signal_detector_interruption(self):
        detector = SignalDetector()
        sig = detector.detect("Sun sun sun...", acoustic_features={"interrupted": True})
        self.assertEqual(sig.signal, "interrupted")

    def test_persona_manager_adaptation_rushed(self):
        gen = PersonaGenerator()
        persona = gen.generate_persona(self.sample_sellers[1])
        orig_pace = persona.pace

        manager = PersonaManager(persona)
        detector = SignalDetector()
        rushed_signal = detector.detect("Bolo jaldi mere paas time nahi hai")

        event = manager.adapt(rushed_signal, turn_number=2)
        self.assertIsNotNone(event)
        self.assertGreater(manager.active_persona.pace, orig_pace)
        self.assertEqual(event.signal_detected, "rushed")
        self.assertEqual(len(manager.trajectory), 1)

    def test_persona_manager_adaptation_frustrated(self):
        gen = PersonaGenerator()
        persona = gen.generate_persona(self.sample_sellers[1])

        manager = PersonaManager(persona)
        detector = SignalDetector()
        frustrated_signal = detector.detect("Bakwas mat karo bar bar phone karke!")

        event = manager.adapt(frustrated_signal, turn_number=2)
        self.assertIsNotNone(event)
        self.assertEqual(manager.active_persona.tone, "empathetic_problem_solver")
        self.assertEqual(manager.active_persona.script_strategy, "problem_solving")
        self.assertIn("frustration", event.adaptation_rationale.lower())

    def test_persona_memory_evolution(self):
        temp_dir = tempfile.mkdtemp()
        temp_mem_file = os.path.join(temp_dir, "test_memory.json")

        try:
            store = PersonaMemoryStore(storage_path=temp_mem_file)
            gen = PersonaGenerator()
            seller = self.sample_sellers[1]
            sid = str(seller["fk_glusr_usr_id"])

            p_init = gen.generate_persona(seller)
            p_final = gen.generate_persona(seller)
            p_final.pace = 1.10
            p_final.tone = "direct_closing"

            mem = store.record_call(
                seller_id=sid,
                disposition="meeting_fixed",
                initial_persona=p_init,
                final_persona=p_final,
                signals_encountered=["rushed", "engaged"],
                notes="Successful fast call"
            )

            self.assertEqual(mem.total_calls, 1)
            self.assertEqual(mem.successful_calls, 1)
            self.assertEqual(mem.preferred_pace, 1.10)
            self.assertEqual(mem.preferred_tone, "direct_closing")

            p_new = gen.generate_persona(seller)
            p_evolved = store.apply_memory_to_persona(p_new)
            self.assertEqual(p_evolved.pace, 1.10)
            self.assertEqual(p_evolved.tone, "direct_closing")
            self.assertIn("memory_evolution", p_evolved.rationale)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_call_simulator_full_flow(self):
        temp_dir = tempfile.mkdtemp()
        temp_mem_file = os.path.join(temp_dir, "sim_test_memory.json")

        try:
            store = PersonaMemoryStore(storage_path=temp_mem_file)
            sim = CallSimulator(sarvam_client=self.mock_sarvam, memory_store=store)

            seller = self.sample_sellers[0]
            result = sim.run_simulation(seller, generate_audio=True)

            self.assertEqual(result.seller_id, str(seller["fk_glusr_usr_id"]))
            self.assertGreaterEqual(result.total_turns, 4)
            self.assertGreaterEqual(len(result.trajectory), 1)
            self.assertNotEqual(result.disposition, "")

            for turn in result.turns:
                self.assertIn(turn.speaker, ["bot", "seller"])
                self.assertGreater(len(turn.text), 0)
                if turn.speaker == "bot":
                    self.assertIsNotNone(turn.audio_base64)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_sarvam_tools(self):
        from src.sarvam_tools import (
            get_seller_profile,
            get_verified_buyer_leads,
            get_official_pricing,
            book_relationship_manager_slot,
            check_dnd_compliance
        )
        # 1. Profile lookup
        prof = get_seller_profile("241241351")
        self.assertIn("top_category", prof)
        self.assertIn("annual_turnover", prof)

        # 2. Verified buyer leads
        leads = get_verified_buyer_leads("Cotton Yarn", "Surat")
        self.assertGreater(leads["active_verified_buyers"], 0)
        self.assertIn("Surat", leads["high_demand_clusters"])
        self.assertIn("100% Mobile OTP", leads["verification_standard"])

        # 3. Official pricing
        pricing = get_official_pricing("0 - 40 L")
        self.assertEqual(pricing["recommended_package"], "Mini Leader")
        self.assertIn("Mini Leader", pricing["tiers"])
        self.assertEqual(pricing["tiers"]["Mini Leader"]["annual_cost_inr"], 28000)

        # 4. Appointment booking
        booking = book_relationship_manager_slot("241241351", "Monday", "11:00 AM", "phone")
        self.assertEqual(booking["status"], "confirmed")
        self.assertIn("IM-RM-", booking["booking_id"])

        # 5. DND Compliance
        dnd = check_dnd_compliance("241241351")
        self.assertTrue(dnd["calling_window_allowed"])
        self.assertIn("09:00 AM - 08:00 PM IST", dnd["calling_hours"])

    def test_sarvam_agent_spec(self):
        spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sarvam_agent_spec.json")
        self.assertTrue(os.path.exists(spec_path))
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)
        self.assertEqual(spec["agent_name"], "IndiaMART VANI Voice Agent")
        self.assertEqual(spec["model_config"]["model"], "sarvam-105b-conversations")
        self.assertEqual(spec["voice_config"]["model"], "bulbul:v4-flash")
        self.assertIn("shubh_enhi_ads", spec["voice_config"]["speaker"])
        self.assertGreaterEqual(len(spec["model_config"]["tools"]), 5)
        self.assertIn("on_start", spec["hooks"])
        self.assertIn("on_end", spec["hooks"])


if __name__ == "__main__":
    unittest.main()

