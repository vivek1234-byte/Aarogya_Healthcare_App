import 'package:flutter/material.dart';
import '../core/services/api_service.dart';
import '../models/triage_session.dart';

class TriageProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();

  String? _activeSessionId;
  String _patientPseudonym = 'PATIENT-001';
  int _patientAge = 45;
  String _patientGender = 'Female';
  String _villageId = 'VILL-UP-RAMPUR-01';

  bool _isRecording = false;
  bool _isLoading = false;
  String? _lastSpokenTranscript;
  TriageTurnResponse? _currentTurnResponse;
  final List<String> _cumulativeSymptoms = [];
  final List<String> _cumulativeDangerSigns = [];

  // Getters
  String? get activeSessionId => _activeSessionId;
  String get patientPseudonym => _patientPseudonym;
  int get patientAge => _patientAge;
  String get patientGender => _patientGender;
  String get villageId => _villageId;
  bool get isRecording => _isRecording;
  bool get isLoading => _isLoading;
  String? get lastSpokenTranscript => _lastSpokenTranscript;
  TriageTurnResponse? get currentTurnResponse => _currentTurnResponse;
  List<String> get cumulativeSymptoms => _cumulativeSymptoms;
  List<String> get cumulativeDangerSigns => _cumulativeDangerSigns;
  bool get isFinal => _currentTurnResponse?.isFinal ?? false;
  String? get triageLevel => _currentTurnResponse?.triageLevel;

  void setPatientDetails({
    required String pseudonym,
    required int age,
    required String gender,
    required String villageId,
  }) {
    _patientPseudonym = pseudonym;
    _patientAge = age;
    _patientGender = gender;
    _villageId = villageId;
    notifyListeners();
  }

  Future<void> startNewSession() async {
    _isLoading = true;
    _currentTurnResponse = null;
    _lastSpokenTranscript = null;
    _cumulativeSymptoms.clear();
    _cumulativeDangerSigns.clear();
    notifyListeners();

    final result = await _apiService.startTriageSession(
      patientId: 'patient-id-uuid',
      patientPseudonym: _patientPseudonym,
      age: _patientAge,
      gender: _patientGender,
      villageId: _villageId,
      language: 'hi',
    );

    _activeSessionId = result['session_id'];
    _isLoading = false;
    notifyListeners();
  }

  void toggleRecording() {
    _isRecording = !_isRecording;
    notifyListeners();
  }

  Future<void> submitSpeechText(String spokenText) async {
    if (_activeSessionId == null) {
      await startNewSession();
    }

    _isLoading = true;
    _lastSpokenTranscript = spokenText;
    notifyListeners();

    final response = await _apiService.processTriageTextTurn(
      sessionId: _activeSessionId!,
      text: spokenText,
    );

    _currentTurnResponse = response;
    for (var s in response.extractedSymptoms) {
      if (!_cumulativeSymptoms.contains(s)) _cumulativeSymptoms.add(s);
    }
    for (var d in response.dangerSigns) {
      if (!_cumulativeDangerSigns.contains(d)) _cumulativeDangerSigns.add(d);
    }

    _isLoading = false;
    notifyListeners();
  }

  void resetTriage() {
    _activeSessionId = null;
    _currentTurnResponse = null;
    _lastSpokenTranscript = null;
    _cumulativeSymptoms.clear();
    _cumulativeDangerSigns.clear();
    _isRecording = false;
    _isLoading = false;
    notifyListeners();
  }
}
