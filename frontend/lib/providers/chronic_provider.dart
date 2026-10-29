import 'package:flutter/material.dart';
import '../core/services/api_service.dart';
import '../models/chronic_models.dart';

class ChronicProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();

  bool _isLoading = false;
  List<ChronicActionItem> _actionQueue = [];
  String _selectedFilter = 'ALL'; // ALL, CRITICAL, HIGH, MODERATE
  VoiceCheckinResult? _lastCheckinResult;

  // 30-day vitals series for plotting
  List<VitalsPoint> _vitalsHistory = [];

  bool get isLoading => _isLoading;
  List<ChronicActionItem> get actionQueue => _actionQueue;
  String get selectedFilter => _selectedFilter;
  VoiceCheckinResult? get lastCheckinResult => _lastCheckinResult;
  List<VitalsPoint> get vitalsHistory => _vitalsHistory;

  List<ChronicActionItem> get filteredQueue {
    if (_selectedFilter == 'ALL') return _actionQueue;
    return _actionQueue.where((item) => item.riskLevel.toUpperCase() == _selectedFilter).toList();
  }

  ChronicProvider() {
    _initSampleVitalsHistory();
    loadActionQueue('VILL-UP-RAMPUR-01');
  }

  void setFilter(String filter) {
    _selectedFilter = filter;
    notifyListeners();
  }

  void _initSampleVitalsHistory() {
    final now = DateTime.now();
    _vitalsHistory = [
      VitalsPoint(date: now.subtract(const Duration(days: 28)), systolic: 124, diastolic: 80, glucose: 110),
      VitalsPoint(date: now.subtract(const Duration(days: 24)), systolic: 126, diastolic: 82, glucose: 114),
      VitalsPoint(date: now.subtract(const Duration(days: 20)), systolic: 128, diastolic: 84, glucose: 120),
      VitalsPoint(date: now.subtract(const Duration(days: 16)), systolic: 134, diastolic: 88, glucose: 132),
      VitalsPoint(date: now.subtract(const Duration(days: 12)), systolic: 142, diastolic: 92, glucose: 148),
      VitalsPoint(date: now.subtract(const Duration(days: 8)), systolic: 148, diastolic: 94, glucose: 162),
      VitalsPoint(date: now.subtract(const Duration(days: 4)), systolic: 154, diastolic: 96, glucose: 175),
      VitalsPoint(date: now, systolic: 162, diastolic: 98, glucose: 188),
    ];
  }

  Future<void> loadActionQueue(String villageId) async {
    _isLoading = true;
    notifyListeners();

    _actionQueue = await _apiService.fetchAshaActionQueue(villageId: villageId);
    _isLoading = false;
    notifyListeners();
  }

  Future<void> submitVoiceCheckin({
    required String patientId,
    required String speechText,
  }) async {
    _isLoading = true;
    notifyListeners();

    _lastCheckinResult = await _apiService.submitVoiceCheckin(
      patientId: patientId,
      speechTranscript: speechText,
    );

    // If new reading arrived, update local plot
    if (_lastCheckinResult?.systolicBp != null) {
      _vitalsHistory.add(VitalsPoint(
        date: DateTime.now(),
        systolic: _lastCheckinResult!.systolicBp!.toDouble(),
        diastolic: _lastCheckinResult!.diastolicBp?.toDouble() ?? 85.0,
        glucose: _lastCheckinResult!.bloodGlucose,
      ));
    }

    _isLoading = false;
    notifyListeners();
  }

  void markActionDone(String patientId) {
    _actionQueue.removeWhere((item) => item.patientId == patientId);
    notifyListeners();
  }
}
