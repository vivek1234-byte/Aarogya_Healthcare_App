import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/theme_provider.dart';
import '../providers/chronic_provider.dart';
import '../models/chronic_models.dart';

class AshaActionRosterScreen extends StatefulWidget {
  const AshaActionRosterScreen({super.key});

  @override
  State<AshaActionRosterScreen> createState() => _AshaActionRosterScreenState();
}

class _AshaActionRosterScreenState extends State<AshaActionRosterScreen> {
  String _selectedFilter = 'ALL';
  String _searchQuery = '';
  final Set<String> _completedVisitIds = {};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<ChronicProvider>(context, listen: false).loadVillageActionQueue();
    });
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;
    final textTheme = Theme.of(context).textTheme;
    final chronicProvider = Provider.of<ChronicProvider>(context);

    // Filter patients based on tab and search
    final items = chronicProvider.actionQueue.where((item) {
      if (_selectedFilter != 'ALL' && item.riskLevel != _selectedFilter) {
        return false;
      }
      if (_searchQuery.isNotEmpty &&
          !item.pseudonymId.toLowerCase().contains(_searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('ASHA Daily Action Roster'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Sync Queue',
            onPressed: () {
              chronicProvider.loadVillageActionQueue();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Action roster synchronized with Sub-centre gateway'),
                  duration: Duration(seconds: 2),
                ),
              );
            },
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isTabletOrWide = constraints.maxWidth >= 700;

          return RefreshIndicator(
            onRefresh: () => chronicProvider.loadVillageActionQueue(),
            child: ListView(
              padding: EdgeInsets.symmetric(
                horizontal: isTabletOrWide ? 32.0 : 16.0,
                vertical: 16.0,
              ),
              children: [
                // Header Banner: Village context and completed counter
                _buildRosterHeader(context, isDark, items.length, chronicProvider.actionQueue.length),
                const SizedBox(height: 16),

                // Search Bar
                _buildSearchBar(context, isDark),
                const SizedBox(height: 14),

                // Filter Chips
                _buildFilterChips(context, isDark, chronicProvider.actionQueue),
                const SizedBox(height: 16),

                // Patient Priority Cards
                if (chronicProvider.isLoading)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 40),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (items.isEmpty)
                  _buildEmptyState(context, isDark)
                else
                  ...items.map((item) => _buildPatientActionCard(
                        context: context,
                        item: item,
                        isDark: isDark,
                        isDone: _completedVisitIds.contains(item.patientId),
                      )),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildRosterHeader(BuildContext context, bool isDark, int visibleCount, int totalCount) {
    final completedCount = _completedVisitIds.length;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1C2723) : const Color(0xFFE8F5E9),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppColors.primaryGreen.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.primaryGreen.withOpacity(0.18),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.assignment_turned_in_rounded, color: AppColors.primaryGreen, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Rampur Sub-Centre • Today\'s Targets',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
                const SizedBox(height: 4),
                Text(
                  '$completedCount of $totalCount home visits completed today',
                  style: TextStyle(
                    fontSize: 13,
                    color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                  ),
                ),
              ],
            ),
          ),
          // Progress Percentage Pill
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.primaryGreen,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              totalCount == 0 ? '0%' : '${((completedCount / totalCount) * 100).toInt()}%',
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar(BuildContext context, bool isDark) {
    return TextField(
      onChanged: (val) {
        setState(() {
          _searchQuery = val;
        });
      },
      decoration: InputDecoration(
        hintText: 'Search by pseudonym ID (e.g. HASH-RAMPUR)...',
        prefixIcon: const Icon(Icons.search_rounded),
        suffixIcon: _searchQuery.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.clear_rounded),
                onPressed: () {
                  setState(() {
                    _searchQuery = '';
                  });
                },
              )
            : null,
      ),
    );
  }

  Widget _buildFilterChips(BuildContext context, bool isDark, List<ChronicActionItem> allItems) {
    final criticalCount = allItems.where((e) => e.riskLevel == 'CRITICAL').length;
    final highCount = allItems.where((e) => e.riskLevel == 'HIGH').length;
    final modCount = allItems.where((e) => e.riskLevel == 'MODERATE').length;

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _filterChip('ALL', 'All (${allItems.length})', isDark),
          const SizedBox(width: 8),
          _filterChip('CRITICAL', 'Critical ($criticalCount)', isDark, AppColors.emergencyRed),
          const SizedBox(width: 8),
          _filterChip('HIGH', 'High ($highCount)', isDark, AppColors.urgentOrange),
          const SizedBox(width: 8),
          _filterChip('MODERATE', 'Moderate ($modCount)', isDark, AppColors.warningAmber),
        ],
      ),
    );
  }

  Widget _filterChip(String filterKey, String label, bool isDark, [Color? activeColor]) {
    final isSelected = _selectedFilter == filterKey;
    final color = activeColor ?? AppColors.primaryGreen;

    return ChoiceChip(
      label: Text(
        label,
        style: TextStyle(
          fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
          color: isSelected ? Colors.white : (isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary),
        ),
      ),
      selected: isSelected,
      selectedColor: color,
      backgroundColor: isDark ? AppColors.darkCardBg : AppColors.lightCardBg,
      onSelected: (val) {
        if (val) {
          setState(() {
            _selectedFilter = filterKey;
          });
        }
      },
    );
  }

  Widget _buildPatientActionCard({
    required BuildContext context,
    required ChronicActionItem item,
    required bool isDark,
    required bool isDone,
  }) {
    Color riskColor;
    IconData riskIcon;
    switch (item.riskLevel.toUpperCase()) {
      case 'CRITICAL':
        riskColor = AppColors.emergencyRed;
        riskIcon = Icons.warning_rounded;
        break;
      case 'HIGH':
        riskColor = AppColors.urgentOrange;
        riskIcon = Icons.priority_high_rounded;
        break;
      case 'MODERATE':
        riskColor = AppColors.warningAmber;
        riskIcon = Icons.info_outline_rounded;
        break;
      default:
        riskColor = AppColors.stableGreen;
        riskIcon = Icons.check_circle_outline_rounded;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      elevation: isDone ? 1 : 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: isDone ? Colors.grey.withOpacity(0.3) : riskColor.withOpacity(0.4),
          width: isDone ? 1 : 1.5,
        ),
      ),
      child: AnimatedOpacity(
        duration: const Duration(milliseconds: 250),
        opacity: isDone ? 0.6 : 1.0,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Row: Priority badge, Pseudonym, and Demographics
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: riskColor.withOpacity(0.16),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(riskIcon, color: riskColor, size: 16),
                        const SizedBox(width: 4),
                        Text(
                          item.riskLevel,
                          style: TextStyle(
                            color: riskColor,
                            fontWeight: FontWeight.w800,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      item.pseudonymId,
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Text(
                    '${item.age}y / ${item.gender.substring(0, 1)}',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Recommended Task
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF1E232A) : const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  item.recommendedAction,
                  style: const TextStyle(fontSize: 14, height: 1.35, fontWeight: FontWeight.w500),
                ),
              ),
              const SizedBox(height: 12),

              // Clinical Metric Pills
              Row(
                children: [
                  if (item.latestSystolic != null) ...[
                    _vitalsPill(
                      label: 'Latest Systolic',
                      value: '${item.latestSystolic!.toInt()} mmHg',
                      isAlert: item.latestSystolic! >= 140,
                      isDark: isDark,
                    ),
                    const SizedBox(width: 8),
                  ],
                  if (item.adherenceRatePct != null)
                    _vitalsPill(
                      label: 'Adherence',
                      value: '${item.adherenceRatePct!.toInt()}%',
                      isAlert: item.adherenceRatePct! < 70,
                      isDark: isDark,
                    ),
                ],
              ),

              // Flags
              if (item.flags.isNotEmpty) ...[
                const SizedBox(height: 10),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: item.flags.map((flag) {
                    return Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.emergencyRed.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        flag.replaceAll('_', ' '),
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: AppColors.emergencyRed,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],

              const Divider(height: 24),

              // Bottom Actions: Call and Mark Complete
              Row(
                children: [
                  // Call Patient Button
                  OutlinedButton.icon(
                    onPressed: () => _showCallDialog(context, item),
                    icon: const Icon(Icons.phone_in_talk_rounded, size: 18),
                    label: const Text('Call'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    ),
                  ),
                  const Spacer(),

                  // Mark Done Button
                  ElevatedButton.icon(
                    onPressed: () {
                      setState(() {
                        if (isDone) {
                          _completedVisitIds.remove(item.patientId);
                        } else {
                          _completedVisitIds.add(item.patientId);
                        }
                      });

                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(
                            isDone
                                ? 'Visit marked pending for ${item.pseudonymId}'
                                : 'Home visit logged as completed for ${item.pseudonymId}',
                          ),
                          duration: const Duration(seconds: 2),
                        ),
                      );
                    },
                    icon: Icon(
                      isDone ? Icons.undo_rounded : Icons.check_circle_rounded,
                      size: 18,
                    ),
                    label: Text(isDone ? 'Mark Pending' : 'Mark Visit Done'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isDone ? Colors.grey : AppColors.primaryGreen,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _vitalsPill({
    required String label,
    required String value,
    required bool isAlert,
    required bool isDark,
  }) {
    final alertColor = isAlert ? AppColors.emergencyRed : AppColors.stableGreen;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: alertColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: alertColor.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$label: ',
            style: TextStyle(
              fontSize: 12,
              color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: alertColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context, bool isDark) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 40),
      child: Center(
        child: Column(
          children: [
            Icon(Icons.done_all_rounded, size: 56, color: AppColors.stableGreen.withOpacity(0.7)),
            const SizedBox(height: 12),
            const Text(
              'No visits in this category',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            Text(
              'All targeted patients for this priority level are up to date.',
              style: TextStyle(
                fontSize: 13,
                color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showCallDialog(BuildContext context, ChronicActionItem item) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.phone_rounded, color: AppColors.primaryGreen),
            const SizedBox(width: 8),
            const Text('Dial Patient / Family'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Contacting registered phone for ${item.pseudonymId}'),
            const SizedBox(height: 10),
            const Text(
              'Phone number is securely decrypted on-demand under ASHA role permissions (DPDP Act 2023).',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Calling +91 98765 43210 (${item.pseudonymId})...'),
                  backgroundColor: AppColors.primaryGreen,
                ),
              );
            },
            icon: const Icon(Icons.call_rounded),
            label: const Text('Dial Now'),
          ),
        ],
      ),
    );
  }
}
