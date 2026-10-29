import re
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.base_schema import BaseModel


class ParsedCheckinData(BaseModel):
    raw_transcript: str
    detected_language: str = "hi"
    
    # Extracted vitals
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    blood_glucose: Optional[float] = None
    glucose_context: Optional[str] = None # FASTING, POST_PRANDIAL, RANDOM
    
    # Extracted adherence
    adherence_status: Optional[str] = None # TAKEN, MISSED, SKIPPED
    miss_reason: Optional[str] = None
    medication_name: Optional[str] = None


class VoiceCheckinParser:
    """
    Parses conversational patient/caregiver voice responses during scheduled
    automated check-ins or ASHA assisted chronic reviews.
    """

    @staticmethod
    def parse_checkin_speech(transcript: str, default_language: str = "hi") -> ParsedCheckinData:
        text = transcript.strip().lower()
        result = ParsedCheckinData(raw_transcript=transcript, detected_language=default_language)

        # 1. Parse Blood Pressure (e.g., "140 और 90", "140 बटा 90", "140 by 90", "140/90")
        bp_patterns = [
            r'(\d{2,3})\s*(?:बटा|और|by|/|,|-|\s+)\s*(\d{2,3})',
            r'बीपी\s*(\d{2,3})',
            r'bp\s*(\d{2,3})'
        ]
        for pat in bp_patterns:
            m = re.search(pat, text)
            if m:
                sys_val = int(m.group(1))
                if 70 <= sys_val <= 260:
                    result.systolic_bp = sys_val
                    if len(m.groups()) >= 2 and m.group(2):
                        dia_val = int(m.group(2))
                        if 40 <= dia_val <= 150:
                            result.diastolic_bp = dia_val
                    break

        # 2. Parse Blood Glucose (e.g. "शुगर 165 था", "sugar 150", "खाली पेट 130")
        glu_patterns = [
            r'(?:शुगर|sugar|ग्लूकोज|glucose)\s*(?:स्तर|level)?\s*(\d{2,3})',
            r'(\d{2,3})\s*(?:शुगर|sugar|mg/dl)',
            r'(?:खाली पेट|fasting)\s*(\d{2,3})',
            r'(?:खाने के बाद|post prandial)\s*(\d{2,3})'
        ]
        for pat in glu_patterns:
            m = re.search(pat, text)
            if m:
                val = float(m.group(1))
                if 30 <= val <= 600:
                    result.blood_glucose = val
                    break

        # Glucose context
        if "खाली पेट" in text or "fasting" in text:
            result.glucose_context = "FASTING"
        elif "खाने के बाद" in text or "post prandial" in text or "after food" in text:
            result.glucose_context = "POST_PRANDIAL"
        elif result.blood_glucose:
            result.glucose_context = "RANDOM"

        # 3. Parse Medication Adherence
        taken_indicators = [
            "गोली ले ली", "गोली ली थी", "गोली ली", "दवाई ले ली", "दवाई खाई", "गोली खा ली",
            "दवाई ली", "ले ली थी", "खा ली थी", "ले ली", "खा ली",
            "took medicine", "taken", "took pill", "had medicine", "yes took"
        ]
        missed_indicators = [
            "नहीं ली", "छूट गई", "भूल गया", "दवाई खत्म", "गोली नहीं खाई", "नहीं खाई",
            "missed", "forgot", "did not take", "ran out", "stopped", "not taken"
        ]

        if any(m in text for m in missed_indicators):
            result.adherence_status = "MISSED"
        elif any(t in text for t in taken_indicators) or (("गोली" in text or "दवाई" in text or "pill" in text) and ("ली" in text or "खाई" in text or "took" in text)):
            result.adherence_status = "TAKEN"

        # Identify miss reason if missed
        if result.adherence_status == "MISSED":
            if "खत्म" in text or "ran out" in text or "stock" in text or "नहीं मिली" in text:
                result.miss_reason = "STOCKOUT_OR_SUPPLY_GAP"
            elif "भूल" in text or "forgot" in text:
                result.miss_reason = "FORGOTTEN"
            elif "चक्कर" in text or "side effect" in text or "उल्टी" in text or "परेशानी" in text:
                result.miss_reason = "ADVERSE_EFFECTS"
            else:
                result.miss_reason = "UNSPECIFIED"

        # Check for medication name
        if "बीपी" in text or "bp" in text:
            result.medication_name = "Amlodipine / Telmisartan (Hypertension)"
        elif "शुगर" in text or "sugar" in text or "डायबिटीज" in text:
            result.medication_name = "Metformin / Glimepiride (Diabetes)"

        return result


voice_checkin_parser = VoiceCheckinParser()
