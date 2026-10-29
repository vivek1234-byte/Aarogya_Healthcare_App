import 'dart:io';
import 'package:flutter/foundation.dart';

class ApiConstants {
  // Default Local Gateway
  // Android Emulator maps host machine's localhost to 10.0.2.2
  // Physical device on local Wi-Fi or Linux Desktop uses localhost
  static String get defaultBaseUrl {
    if (kIsWeb) return 'http://localhost:8000/api/v1';
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000/api/v1';
      }
    } catch (_) {}
    return 'http://localhost:8000/api/v1';
  }

  // Endpoints
  static const String health = '/health';
  static const String authLogin = '/auth/login';
  static const String patients = '/patients/';
  
  // Triage Sessions
  static const String triageSessionStart = '/triage/session/start';
  static String triageAudioTurn(String sessionId) => '/triage/session/$sessionId/audio-turn';
  static String triageTextTurn(String sessionId) => '/triage/session/$sessionId/text-turn';
  static String triageComplete(String sessionId) => '/triage/session/$sessionId/complete';

  // Chronic Care
  static const String chronicCheckinVoice = '/chronic/checkin/voice';
  static const String chronicAdherence = '/chronic/adherence';
  static String chronicPatientEval(String patientId) => '/chronic/patients/$patientId/evaluation';
  static String chronicVillageActionQueue(String villageId) => '/chronic/village/$villageId/action-queue';

  // Surveillance & Outbreak Warning
  static const String surveillanceMapFeed = '/surveillance/map/feed';
  static const String surveillanceAlertsActive = '/surveillance/alerts/active';
}
