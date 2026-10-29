import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/theme_provider.dart';
import '../core/services/api_service.dart';
import '../models/outbreak_models.dart';

class OutbreakSurveillanceScreen extends StatefulWidget {
  const OutbreakSurveillanceScreen({super.key});

  @override
  State<OutbreakSurveillanceScreen> createState() => _OutbreakSurveillanceScreenState();
}

class _OutbreakSurveillanceScreenState extends State<OutbreakSurveillanceScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  List<OutbreakAlert> _alerts = [];
  final Map<String, Set<int>> _checkedRrtTasks = {};

  @override
  void initState() {
    super.initState();
    _loadAlerts();
  }

  Future<void> _loadAlerts() async {
    setState(() => _isLoading = true);
    final data = await _apiService.fetchSurveillanceAlerts();
    setState(() {
      _alerts = data;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Village Outbreak Surveillance'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Feed',
            onPressed: _loadAlerts,
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isTabletOrWide = constraints.maxWidth >= 700;

          if (_isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          return RefreshIndicator(
            onRefresh: _loadAlerts,
            child: ListView(
              padding: EdgeInsets.symmetric(
                horizontal: isTabletOrWide ? 32.0 : 16.0,
                vertical: 16.0,
              ),
              children: [
                // Top Banner: IDSP Early Warning summary
                _buildSurveillanceHeader(context, isDark),
                const SizedBox(height: 16),

                // Interactive Radar / Village Map Cluster Visualizer
                _buildVisualClusterRadar(context, isDark),
                const SizedBox(height: 20),

                // Active Outbreak Village Cards
                Text(
                  'Active Spatio-Temporal Anomaly Alerts',
                  style: textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 6),
                Text(
                  'Fused data from PHC clinics, OTC pharmacy sales & school absenteeism',
                  style: textTheme.bodyMedium,
                ),
                const SizedBox(height: 14),

                ..._alerts.map((alert) => _buildAlertCard(context, alert, isDark)),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSurveillanceHeader(BuildContext context, bool isDark) {
    final hasWarning = _alerts.any((a) => a.alertLevel == 'WARNING' || a.alertLevel == 'OUTBREAK');

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: hasWarning
            ? (isDark ? const Color(0xFF2C1E1E) : const Color(0xFFFFEBEE))
            : (isDark ? const Color(0xFF1E2620) : const Color(0xFFE8F5E9)),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: hasWarning ? AppColors.emergencyRed.withOpacity(0.4) : AppColors.primaryGreen.withOpacity(0.4),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: (hasWarning ? AppColors.emergencyRed : AppColors.primaryGreen).withOpacity(0.18),
              shape: BoxShape.circle,
            ),
            child: Icon(
              hasWarning ? Icons.warning_amber_rounded : Icons.health_and_safety_rounded,
              color: hasWarning ? AppColors.emergencyRed : AppColors.primaryGreen,
              size: 28,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  hasWarning ? 'WARNING: Syndrome Cluster Detected' : 'Block Status: Normal Baseline',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                    color: hasWarning ? AppColors.emergencyRed : AppColors.primaryGreen,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'IDSP Syndromic Alert: Rampur ADD spike detected 3.2 days before hospital surge.',
                  style: TextStyle(
                    fontSize: 13,
                    color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVisualClusterRadar(BuildContext context, bool isDark) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.hub_rounded, color: AppColors.primaryGreen, size: 20),
                const SizedBox(width: 8),
                const Text(
                  'Spatio-Temporal Village Radar',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.emergencyRed.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    'Z-Score >= 3.0 Alert',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppColors.emergencyRed,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            // Custom Canvas Painting of Village Nodes and Outbreak Heat Radii
            SizedBox(
              height: 180,
              width: double.infinity,
              child: CustomPaint(
                painter: _VillageRadarPainter(alerts: _alerts, isDark: isDark),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _radarLegend(color: AppColors.emergencyRed, label: 'Warning Zone (Z > 3.0)'),
                const SizedBox(width: 14),
                _radarLegend(color: AppColors.warningAmber, label: 'Watch Zone (Z > 2.0)'),
                const SizedBox(width: 14),
                _radarLegend(color: AppColors.stableGreen, label: 'Normal Baseline'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _radarLegend({required Color color, required String label}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
      ],
    );
  }

  Widget _buildAlertCard(BuildContext context, OutbreakAlert alert, bool isDark) {
    Color levelColor;
    switch (alert.alertLevel.toUpperCase()) {
      case 'OUTBREAK':
      case 'WARNING':
        levelColor = AppColors.emergencyRed;
        break;
      case 'WATCH':
        levelColor = AppColors.warningAmber;
        break;
      default:
        levelColor = AppColors.stableGreen;
    }

    final checkedTasks = _checkedRrtTasks[alert.id] ?? {};

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: levelColor.withOpacity(0.4), width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Row: Level badge, Village name, Z-Score
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: levelColor.withOpacity(0.16),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    alert.alertLevel,
                    style: TextStyle(color: levelColor, fontWeight: FontWeight.w800, fontSize: 13),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    alert.villageName,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF2A2A35) : const Color(0xFFE2E8F0),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    'Z = ${alert.zScore.toStringAsFixed(2)}',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 13,
                      color: levelColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Syndrome & Statistical metrics
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Syndrome Detected',
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        alert.syndrome,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Observed / Baseline',
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${alert.observedCases} cases (exp. ${alert.baselineCases.toStringAsFixed(1)})',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                          color: levelColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Multi-signal Fusion tags
            Text(
              'Fused Triangulation Signals:',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
              ),
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: alert.fusedSignals.map((signal) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: levelColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '• $signal',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: levelColor),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 14),

            // Recommended Immediate Action
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF1E232A) : const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.grey.withOpacity(0.2)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.flash_on_rounded, color: AppColors.urgentOrange, size: 18),
                      SizedBox(width: 6),
                      Text(
                        'Recommended Intervention',
                        style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    alert.recommendedIntervention,
                    style: const TextStyle(fontSize: 13, height: 1.3),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Rapid Response Team (RRT) Action Checklist
            const Text(
              'Rapid Response Team (RRT) Action Checklist:',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
            ),
            const SizedBox(height: 6),
            ...List.generate(alert.rrtChecklist.length, (idx) {
              final isChecked = checkedTasks.contains(idx);
              return InkWell(
                onTap: () {
                  setState(() {
                    if (isChecked) {
                      _checkedRrtTasks[alert.id]?.remove(idx);
                    } else {
                      _checkedRrtTasks.putIfAbsent(alert.id, () => <int>{}).add(idx);
                    }
                  });
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        isChecked ? Icons.check_box_rounded : Icons.check_box_outline_blank_rounded,
                        color: isChecked ? AppColors.primaryGreen : Colors.grey,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          alert.rrtChecklist[idx],
                          style: TextStyle(
                            fontSize: 13,
                            decoration: isChecked ? TextDecoration.lineThrough : null,
                            color: isChecked
                                ? Colors.grey
                                : (isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _VillageRadarPainter extends CustomPainter {
  final List<OutbreakAlert> alerts;
  final bool isDark;

  _VillageRadarPainter({required this.alerts, required this.isDark});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);

    // Radar concentric circles
    final gridPaint = Paint()
      ..color = (isDark ? Colors.white : Colors.black).withOpacity(0.08)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    for (double r = 30; r <= 80; r += 25) {
      canvas.drawCircle(center, r, gridPaint);
    }

    // Grid crosshairs
    canvas.drawLine(Offset(center.dx - 90, center.dy), Offset(center.dx + 90, center.dy), gridPaint);
    canvas.drawLine(Offset(center.dx, center.dy - 80), Offset(center.dx, center.dy + 80), gridPaint);

    // Sub-centre central hub
    final hubPaint = Paint()..color = AppColors.primaryGreen;
    canvas.drawCircle(center, 6, hubPaint);

    // Plot Villages around the Sub-centre hub
    final villagePositions = [
      Offset(center.dx + 48, center.dy - 35), // Rampur
      Offset(center.dx - 55, center.dy + 25), // Shivpur
      Offset(center.dx + 25, center.dy + 55), // Kalyanpur
    ];

    for (int i = 0; i < alerts.length && i < villagePositions.length; i++) {
      final pos = villagePositions[i];
      final alert = alerts[i];

      Color alertColor = alert.alertLevel == 'WARNING'
          ? AppColors.emergencyRed
          : (alert.alertLevel == 'WATCH' ? AppColors.warningAmber : AppColors.stableGreen);

      // Draw heat radius zone
      final heatPaint = Paint()
        ..color = alertColor.withOpacity(0.25)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(pos, 22, heatPaint);

      final heatBorder = Paint()
        ..color = alertColor.withOpacity(0.7)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      canvas.drawCircle(pos, 22, heatBorder);

      // Village node
      final nodePaint = Paint()..color = alertColor;
      canvas.drawCircle(pos, 5, nodePaint);

      // Connector line to PHC hub
      final linePaint = Paint()
        ..color = alertColor.withOpacity(0.3)
        ..strokeWidth = 1.0
        ..style = PaintingStyle.stroke;
      canvas.drawLine(center, pos, linePaint);

      // Text label for Village
      final textSpan = TextSpan(
        text: alert.villageName.split(' ').first,
        style: TextStyle(
          color: isDark ? Colors.white70 : Colors.black87,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      );
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
      )..layout();
      textPainter.paint(canvas, Offset(pos.dx - 18, pos.dy + 24));
    }
  }

  @override
  bool shouldRepaint(covariant _VillageRadarPainter oldDelegate) => true;
}
