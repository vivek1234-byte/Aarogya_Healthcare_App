import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/triage_provider.dart';
import '../providers/theme_provider.dart';

class VoiceTriageScreen extends StatefulWidget {
  const VoiceTriageScreen({super.key});

  @override
  State<VoiceTriageScreen> createState() => _VoiceTriageScreenState();
}

class _VoiceTriageScreenState extends State<VoiceTriageScreen> {
  final TextEditingController _customInputController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final triage = Provider.of<TriageProvider>(context, listen: false);
      if (triage.activeSessionId == null) {
        triage.startNewSession();
      }
    });
  }

  @override
  void dispose() {
    _customInputController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final triage = Provider.of<TriageProvider>(context);
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Voice Triage & Danger Signs', style: TextStyle(fontWeight: FontWeight.w700)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'New Session',
            onPressed: () => triage.resetTriage(),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Patient Demographics Banner
            _buildPatientBanner(triage, isDark),
            const SizedBox(height: 16),

            // Big Central Voice Mic Station
            _buildMicrophoneStation(triage, isDark),
            const SizedBox(height: 16),

            // Quick Symptom Sample Buttons (for fast ASHA field testing)
            _buildQuickSpeechPresets(triage, isDark),
            const SizedBox(height: 16),

            // Extracted Symptoms & Red Flags Tags
            if (triage.cumulativeSymptoms.isNotEmpty) ...[
              _buildExtractedSymptomsView(triage, isDark),
              const SizedBox(height: 16),
            ],

            // Step-by-Step Guided Clinical Clarification Card
            if (!triage.isFinal && triage.currentTurnResponse?.nextQuestion != null) ...[
              _buildGuidedQuestionCard(triage, isDark),
              const SizedBox(height: 16),
            ],

            // Clinical Triage Decision Result (Emergency / Refer / Treat Locally)
            if (triage.isFinal) ...[
              _buildTriageResultCard(triage, isDark),
              const SizedBox(height: 16),
            ],

            // Frontline Checklist Items
            if (triage.currentTurnResponse?.checklist.isNotEmpty ?? false) ...[
              _buildChecklistView(triage, isDark),
              const SizedBox(height: 24),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPatientBanner(TriageProvider triage, bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('ACTIVE ENCOUNTER', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.primaryGreen, letterSpacing: 0.6)),
              const SizedBox(height: 2),
              Text(
                '${triage.patientPseudonym} (${triage.patientAge}y, ${triage.patientGender})',
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
              ),
            ],
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: AppColors.primaryGreen.withOpacity(0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              triage.villageId,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.primaryGreen),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMicrophoneStation(TriageProvider triage, bool isDark) {
    final isRec = triage.isRecording;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isRec ? AppColors.emergencyRed : (isDark ? AppColors.darkBorder : AppColors.lightBorder),
          width: isRec ? 2.0 : 1.2,
        ),
      ),
      child: Column(
        children: [
          Text(
            isRec ? 'सुन रहे हैं... (Listening...)' : 'लक्षण बोलने के लिए माइक दबाएं',
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: isRec ? AppColors.emergencyRed : (isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            isRec ? 'Patient or health worker speaking in Hindi/English' : 'Tap microphone and speak in local language',
            style: TextStyle(fontSize: 13, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
          ),
          const SizedBox(height: 20),

          // Big Circular Pulsing Button
          GestureDetector(
            onTap: () {
              triage.toggleRecording();
              if (triage.isRecording) {
                // Simulate speech capture after 2.5s for demonstration
                Future.delayed(const Duration(milliseconds: 2500), () {
                  if (triage.isRecording) {
                    triage.toggleRecording();
                    triage.submitSpeechText('सीने में दर्द है और पसीना आ रहा है');
                  }
                });
              }
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              width: isRec ? 95 : 85,
              height: isRec ? 95 : 85,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isRec ? AppColors.emergencyRed : AppColors.primaryGreen,
                boxShadow: [
                  BoxShadow(
                    color: (isRec ? AppColors.emergencyRed : AppColors.primaryGreen).withOpacity(0.35),
                    blurRadius: isRec ? 22 : 12,
                    spreadRadius: isRec ? 6 : 2,
                  )
                ],
              ),
              child: Icon(
                isRec ? Icons.stop_rounded : Icons.mic_rounded,
                color: Colors.white,
                size: isRec ? 48 : 42,
              ),
            ),
          ),

          if (triage.lastSpokenTranscript != null) ...[
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: (isDark ? Colors.black : Colors.grey.shade100).withOpacity(0.5),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.record_voice_over_rounded, size: 20, color: AppColors.primaryGreen),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '"${triage.lastSpokenTranscript}"',
                      style: const TextStyle(fontSize: 14, fontStyle: FontStyle.italic, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildQuickSpeechPresets(TriageProvider triage, bool isDark) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Quick Voice Simulation (Tap to Test)',
          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ActionChip(
              avatar: const Icon(Icons.emergency, color: AppColors.emergencyRed, size: 16),
              label: const Text('सीने में दर्द + पसीना (Chest Pain)'),
              onPressed: () => triage.submitSpeechText('सीने में तेज दर्द है और ठंडा पसीना आ रहा है'),
            ),
            ActionChip(
              avatar: const Icon(Icons.child_care, color: AppColors.urgentOrange, size: 16),
              label: const Text('बच्चे को झटके (Child Convulsion)'),
              onPressed: () => triage.submitSpeechText('बच्ची को तेज बुखार है और झटके आ रहे हैं, दूध नहीं पी रही'),
            ),
            ActionChip(
              avatar: const Icon(Icons.thermostat, color: AppColors.secondaryBlue, size: 16),
              label: const Text('हल्का बुखार (Mild Fever)'),
              onPressed: () => triage.submitSpeechText('आज से हल्का बुखार है, गर्दन में कोई अकड़न नहीं है'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildExtractedSymptomsView(TriageProvider triage, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('IDENTIFIED CLINICAL SIGNS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppColors.primaryGreen)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ...triage.cumulativeDangerSigns.map((d) => Chip(
                backgroundColor: AppColors.emergencyRed.withOpacity(0.15),
                side: const BorderSide(color: AppColors.emergencyRed, width: 1.2),
                label: Text(d.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(color: AppColors.emergencyRed, fontWeight: FontWeight.w800, fontSize: 12)),
              )),
              ...triage.cumulativeSymptoms.where((s) => !triage.cumulativeDangerSigns.contains(s)).map((s) => Chip(
                backgroundColor: isDark ? AppColors.darkBorder : Colors.grey.shade200,
                label: Text(s.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              )),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildGuidedQuestionCard(TriageProvider triage, bool isDark) {
    final nextQ = triage.currentTurnResponse?.nextQuestion ?? '';

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.secondaryBlue.withOpacity(isDark ? 0.15 : 0.08),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.secondaryBlue.withOpacity(0.4), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: const BoxDecoration(color: AppColors.secondaryBlue, shape: BoxShape.circle),
                child: const Icon(Icons.help_outline, color: Colors.white, size: 18),
              ),
              const SizedBox(width: 8),
              const Text('GUIDED CLINICAL QUESTION', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12, color: AppColors.secondaryBlue)),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            nextQ,
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700, height: 1.35),
          ),
          const SizedBox(height: 14),

          // Big Easy Touch Reply Buttons
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.check, size: 20),
                  label: const Text('हां (Yes)'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryGreen,
                    minimumSize: const Size(0, 48),
                  ),
                  onPressed: () => triage.submitSpeechText('हां, यह लक्षण मौजूद है (Yes)'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.close, size: 20),
                  label: const Text('नहीं (No)'),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size(0, 48),
                    side: const BorderSide(color: AppColors.lightTextSecondary, width: 1.5),
                  ),
                  onPressed: () => triage.submitSpeechText('नहीं, ऐसा कुछ नहीं है (No)'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTriageResultCard(TriageProvider triage, bool isDark) {
    final level = triage.triageLevel ?? 'HOME_CARE';
    final isEmergency = level == 'EMERGENCY';
    final isRefer = level == 'REFER';

    final Color badgeColor = isEmergency
        ? AppColors.emergencyRed
        : (isRefer ? AppColors.urgentOrange : AppColors.stableGreen);

    final String titleText = isEmergency
        ? '🚨 EMERGENCY RED FLAG'
        : (isRefer ? '⚠️ REFERRAL REQUIRED' : '✅ TREAT LOCALLY (ASHA PROTOCOL)');

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: badgeColor.withOpacity(isDark ? 0.2 : 0.1),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: badgeColor, width: 2.0),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                titleText,
                style: TextStyle(color: badgeColor, fontWeight: FontWeight.w900, fontSize: 18),
              ),
              if (triage.currentTurnResponse?.isRedFlagOverridden ?? false)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: badgeColor, borderRadius: BorderRadius.circular(6)),
                  child: const Text('RULE OVERRIDE', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800)),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            triage.currentTurnResponse?.decisionRationale ?? '',
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, height: 1.4),
          ),
          const SizedBox(height: 14),

          // Action Buttons
          if (isEmergency)
            ElevatedButton.icon(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Dispatching 108 Emergency Ambulance...'), backgroundColor: AppColors.emergencyRed),
                );
              },
              icon: const Icon(Icons.phone_in_talk, size: 22),
              label: const Text('CALL 108 AMBULANCE NOW', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.emergencyRed, minimumSize: const Size(double.infinity, 52)),
            ),

          if (isRefer && !isEmergency)
            ElevatedButton.icon(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Doctor summary sent to PHC escalation queue')),
                );
              },
              icon: const Icon(Icons.description, size: 20),
              label: const Text('VIEW 1-PAGE DOCTOR SUMMARY'),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.urgentOrange, minimumSize: const Size(double.infinity, 50)),
            ),
        ],
      ),
    );
  }

  Widget _buildChecklistView(TriageProvider triage, bool isDark) {
    final items = triage.currentTurnResponse?.checklist ?? [];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('FRONTLINE STABILIZATION CHECKLIST', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.primaryGreen)),
          const SizedBox(height: 10),
          ...items.map((item) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 4.0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.check_circle_outline, size: 20, color: AppColors.primaryGreen),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(item, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                ),
              ],
            ),
          )),
        ],
      ),
    );
  }
}
