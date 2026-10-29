import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/chronic_provider.dart';
import '../providers/theme_provider.dart';
import '../models/chronic_models.dart';

class ChronicCareScreen extends StatelessWidget {
  const ChronicCareScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final chronic = Provider.of<ChronicProvider>(context);
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Chronic Care & Vitals Curves', style: TextStyle(fontWeight: FontWeight.w700)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Patient Header
            _buildPatientHeader(isDark),
            const SizedBox(height: 16),

            // Early Deterioration Alert Banner (Objective O2: >= 7 days early)
            _buildEarlyWarningBanner(context, isDark),
            const SizedBox(height: 16),

            // Latest Observations Metric Cards (BP, Glucose, Adherence)
            _buildVitalsSummaryRow(chronic, isDark),
            const SizedBox(height: 20),

            // 30-Day Blood Pressure & Glucose Trend Graph
            _buildVitalsTrendCard(chronic, isDark),
            const SizedBox(height: 20),

            // Voice Check-in Card (Speech Parser UI)
            _buildVoiceCheckinSection(context, chronic, isDark),
          ],
        ),
      ),
    );
  }

  Widget _buildPatientHeader(bool isDark) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: const Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('MONITORED CHRONIC COHORT', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.secondaryBlue, letterSpacing: 0.6)),
              SizedBox(height: 3),
              Text('HASH-RAMPUR-101 (58y, Male)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
              Text('Diagnosis: Essential Hypertension & Type 2 Diabetes', style: TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
          Chip(
            label: Text('Next Visit: 12d', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }

  Widget _buildEarlyWarningBanner(BuildContext context, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.urgentOrange.withOpacity(isDark ? 0.2 : 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.urgentOrange, width: 1.5),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.warning_amber_rounded, color: AppColors.urgentOrange, size: 28),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Deterioration Detected (12 Days Lead Time)',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppColors.urgentOrange),
                ),
                SizedBox(height: 4),
                Text(
                  'Systolic BP velocity (+2.5 mmHg/day) combined with missed medication detected. ASHA home review recommended before Day 30 clinic visit.',
                  style: TextStyle(fontSize: 13, height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVitalsSummaryRow(ChronicProvider chronic, bool isDark) {
    final latest = chronic.vitalsHistory.isNotEmpty ? chronic.vitalsHistory.last : null;
    final sys = latest != null ? '${latest.systolic.toInt()}/${latest.diastolic.toInt()}' : '154/96';
    final glu = latest?.glucose != null ? '${latest!.glucose!.toInt()} mg/dL' : '175 mg/dL';

    return Row(
      children: [
        // Blood Pressure
        Expanded(
          child: _buildMetricTile(
            title: 'Blood Pressure',
            value: sys,
            subtitle: 'Stage 2 HTN',
            color: AppColors.emergencyRed,
            isDark: isDark,
          ),
        ),
        const SizedBox(width: 10),
        // Fasting Blood Glucose
        Expanded(
          child: _buildMetricTile(
            title: 'Fasting Glucose',
            value: glu,
            subtitle: 'Hyperglycemia',
            color: AppColors.urgentOrange,
            isDark: isDark,
          ),
        ),
        const SizedBox(width: 10),
        // Medication Adherence
        Expanded(
          child: _buildMetricTile(
            title: 'Adherence',
            value: '60%',
            subtitle: '2 Doses Missed',
            color: AppColors.warningAmber,
            isDark: isDark,
          ),
        ),
      ],
    );
  }

  Widget _buildMetricTile({
    required String title,
    required String value,
    required String subtitle,
    required Color color,
    required bool isDark,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontSize: 11, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: color)),
          const SizedBox(height: 2),
          Text(subtitle, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color)),
        ],
      ),
    );
  }

  Widget _buildVitalsTrendCard(ChronicProvider chronic, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('30-DAY BLOOD PRESSURE CURVE', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.secondaryBlue)),
              Text('Red line = 140 mmHg limit', style: TextStyle(fontSize: 11, color: AppColors.emergencyRed, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 16),

          // Custom Clean Canvas Curve Rendering
          SizedBox(
            height: 160,
            width: double.infinity,
            child: CustomPaint(
              painter: _BPCurvePainter(
                points: chronic.vitalsHistory,
                isDark: isDark,
              ),
            ),
          ),
          const SizedBox(height: 12),

          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildLegendDot(AppColors.primaryGreen, 'Systolic BP (mmHg)'),
              const SizedBox(width: 20),
              _buildLegendDot(AppColors.secondaryBlue, 'Diastolic BP (mmHg)'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegendDot(Color color, String label) {
    return Row(
      children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
      ],
    );
  }

  Widget _buildVoiceCheckinSection(BuildContext context, ChronicProvider chronic, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('VOICE CHECK-IN & PILL LOGGING', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.primaryGreen)),
          const SizedBox(height: 6),
          const Text('Spoken reading parser for rural patients or ASHA visits', style: TextStyle(fontSize: 13, color: Colors.grey)),
          const SizedBox(height: 14),

          // Presets to simulate patient voice response
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ElevatedButton.icon(
                icon: const Icon(Icons.mic, size: 18),
                label: const Text('बीपी 145/92 था, गोली ले ली थी'),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(0, 44),
                  backgroundColor: AppColors.primaryGreen,
                ),
                onPressed: () {
                  chronic.submitVoiceCheckin(
                    patientId: 'p-001',
                    speechText: 'आज सुबह बीपी 145 बटा 92 आया था और गोली ले ली थी',
                  );
                },
              ),
              OutlinedButton.icon(
                icon: const Icon(Icons.medication_liquid, size: 18),
                label: const Text('दवाई खत्म हो गई, नहीं ली'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(0, 44),
                  side: const BorderSide(color: AppColors.urgentOrange),
                ),
                onPressed: () {
                  chronic.submitVoiceCheckin(
                    patientId: 'p-001',
                    speechText: 'दवाई खत्म हो गई थी तो नहीं ली, खाली पेट शुगर 168 था',
                  );
                },
              ),
            ],
          ),

          if (chronic.lastCheckinResult != null) ...[
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primaryGreen.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.record_voice_over, color: AppColors.primaryGreen),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      chronic.lastCheckinResult!.voiceFeedbackTextHi,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
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
}

class _BPCurvePainter extends CustomPainter {
  final List<VitalsPoint> points;
  final bool isDark;

  _BPCurvePainter({required this.points, required this.isDark});

  @override
  void paint(Canvas canvas, Size size) {
    if (points.isEmpty) return;

    final sysPaint = Paint()
      ..color = AppColors.primaryGreen
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;

    final diaPaint = Paint()
      ..color = AppColors.secondaryBlue
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke;

    final limitPaint = Paint()
      ..color = AppColors.emergencyRed.withOpacity(0.6)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    // Draw 140 mmHg limit horizontal line
    const double minBp = 60.0;
    const double maxBp = 190.0;

    double getY(double bp) => size.height - ((bp - minBp) / (maxBp - minBp) * size.height);

    final limitY = getY(140.0);
    canvas.drawLine(Offset(0, limitY), Offset(size.width, limitY), limitPaint);

    // Draw Systolic & Diastolic lines
    final sysPath = Path();
    final diaPath = Path();

    final stepX = size.width / (points.length - 1);

    for (int i = 0; i < points.length; i++) {
      final x = i * stepX;
      final sysY = getY(points[i].systolic);
      final diaY = getY(points[i].diastolic);

      if (i == 0) {
        sysPath.moveTo(x, sysY);
        diaPath.moveTo(x, diaY);
      } else {
        sysPath.lineTo(x, sysY);
        diaPath.lineTo(x, diaY);
      }

      // Draw dot on points
      canvas.drawCircle(Offset(x, sysY), 4, Paint()..color = AppColors.primaryGreen);
      canvas.drawCircle(Offset(x, diaY), 3.5, Paint()..color = AppColors.secondaryBlue);
    }

    canvas.drawPath(sysPath, sysPaint);
    canvas.drawPath(diaPath, diaPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
