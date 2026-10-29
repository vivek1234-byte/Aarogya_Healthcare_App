import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/theme_provider.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _mobileController = TextEditingController(text: '9876543210');
  final _passwordController = TextEditingController(text: '1234');
  
  bool _isOtherLogin = false; // When true: shows "OR Login as" role options; when false: hidden
  String _selectedOtherRole = 'Health Worker'; // 'Health Worker', 'Doctor', 'Health Officer', 'Patient / Family'
  bool _obscurePassword = true;
  bool _isLoading = false;

  @override
  void dispose() {
    _mobileController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _onToggleLoginType(bool isOther) {
    setState(() {
      _isOtherLogin = isOther;
      if (!isOther) {
        _mobileController.text = '9876543210';
      } else {
        _onSelectOtherRole(_selectedOtherRole);
      }
    });
  }

  void _onSelectOtherRole(String role) {
    setState(() {
      _selectedOtherRole = role;
      if (role == 'Health Worker') {
        _mobileController.text = 'ASHA-RAMPUR-7821';
      } else if (role == 'Doctor') {
        _mobileController.text = 'DR-VERMA-PHC-402';
      } else if (role == 'Health Officer') {
        _mobileController.text = 'OFFICER-DIST-881';
      } else {
        _mobileController.text = 'PATIENT-FAM-552';
      }
    });
  }

  Future<void> _handleLogIn() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    await Future.delayed(const Duration(milliseconds: 600));

    if (!mounted) return;
    setState(() => _isLoading = false);

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;
    final size = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0F172A) : const Color(0xFFE4F1E9),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF1E293B) : const Color(0xFFF2F9F4),
                  borderRadius: BorderRadius.circular(36),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF1E824C).withOpacity(0.18),
                      blurRadius: 35,
                      offset: const Offset(0, 15),
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(36),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // ==========================================
                      // 1. EXACT TOP HERO ARTWORK (100% MATCH)
                      // ==========================================
                      Image.asset(
                        'assets/images/exact_top_hero.jpg',
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),

                      // ==========================================
                      // 2. BOTTOM FLOATING WHITE LOGIN SHEET
                      // ==========================================
                      Transform.translate(
                        offset: const Offset(0, -22),
                        child: Container(
                          padding: const EdgeInsets.fromLTRB(22, 22, 22, 20),
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF1E293B) : Colors.white,
                            borderRadius: const BorderRadius.only(
                              topLeft: Radius.circular(36),
                              topRight: Radius.circular(36),
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.06),
                                blurRadius: 15,
                                offset: const Offset(0, -4),
                              ),
                            ],
                          ),
                          child: Form(
                            key: _formKey,
                            child: Column(
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              // Title & Subtitle
                              Text(
                                'Welcome Back',
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w900,
                                  color: isDark ? Colors.white : const Color(0xFF111827),
                                  letterSpacing: -0.5,
                                ),
                              ),
                              const SizedBox(height: 3),
                              Text(
                                'Log in to continue',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF6B7280),
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              const SizedBox(height: 16),

                              // Two Top Toggle Pills: [ 👤 Patient ]  [ 🧑‍⚕️ Other Login ]
                              Container(
                                padding: const EdgeInsets.all(4),
                                decoration: BoxDecoration(
                                  color: isDark ? const Color(0xFF0F172A) : const Color(0xFFF1F5F9),
                                  borderRadius: BorderRadius.circular(24),
                                ),
                                child: Row(
                                  children: [
                                    // Patient Tab
                                    Expanded(
                                      child: GestureDetector(
                                        onTap: () => _onToggleLoginType(false),
                                        child: AnimatedContainer(
                                          duration: const Duration(milliseconds: 200),
                                          padding: const EdgeInsets.symmetric(vertical: 10),
                                          decoration: BoxDecoration(
                                            color: !_isOtherLogin ? const Color(0xFF1E824C) : Colors.transparent,
                                            borderRadius: BorderRadius.circular(20),
                                            boxShadow: !_isOtherLogin
                                                ? [
                                                    BoxShadow(
                                                      color: const Color(0xFF1E824C).withOpacity(0.35),
                                                      blurRadius: 8,
                                                      offset: const Offset(0, 2),
                                                    ),
                                                  ]
                                                : [],
                                          ),
                                          child: Row(
                                            mainAxisAlignment: MainAxisAlignment.center,
                                            children: [
                                              Icon(
                                                Icons.person_rounded,
                                                size: 16,
                                                color: !_isOtherLogin ? Colors.white : Colors.grey.shade600,
                                              ),
                                              const SizedBox(width: 6),
                                              Text(
                                                'Patient / Family',
                                                style: TextStyle(
                                                  fontSize: 12,
                                                  fontWeight: FontWeight.w800,
                                                  color: !_isOtherLogin ? Colors.white : Colors.grey.shade600,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ),

                                    // Other Login Tab
                                    Expanded(
                                      child: GestureDetector(
                                        onTap: () => _onToggleLoginType(true),
                                        child: AnimatedContainer(
                                          duration: const Duration(milliseconds: 200),
                                          padding: const EdgeInsets.symmetric(vertical: 10),
                                          decoration: BoxDecoration(
                                            color: _isOtherLogin ? const Color(0xFF1E824C) : Colors.transparent,
                                            borderRadius: BorderRadius.circular(20),
                                            boxShadow: _isOtherLogin
                                                ? [
                                                    BoxShadow(
                                                      color: const Color(0xFF1E824C).withOpacity(0.35),
                                                      blurRadius: 8,
                                                      offset: const Offset(0, 2),
                                                    ),
                                                  ]
                                                : [],
                                          ),
                                          child: Row(
                                            mainAxisAlignment: MainAxisAlignment.center,
                                            children: [
                                              Icon(
                                                Icons.medical_services_outlined,
                                                size: 16,
                                                color: _isOtherLogin ? Colors.white : Colors.grey.shade600,
                                              ),
                                              const SizedBox(width: 6),
                                              Text(
                                                'Other Login',
                                                style: TextStyle(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w800,
                                                  color: _isOtherLogin ? Colors.white : Colors.grey.shade600,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 16),

                              // Mobile Number Input
                              TextFormField(
                                controller: _mobileController,
                                decoration: InputDecoration(
                                  hintText: _isOtherLogin ? 'Worker ID / Mobile Number' : 'Mobile Number',
                                  prefixIcon: const Icon(Icons.phone_outlined, size: 20, color: Color(0xFF64748B)),
                                  filled: true,
                                  fillColor: isDark ? const Color(0xFF0F172A) : const Color(0xFFF8FAFC),
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                  enabledBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(16),
                                    borderSide: BorderSide(color: isDark ? const Color(0xFF334155) : const Color(0xFFE2E8F0)),
                                  ),
                                  focusedBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(16),
                                    borderSide: const BorderSide(color: Color(0xFF1E824C), width: 1.8),
                                  ),
                                ),
                                validator: (v) => (v == null || v.trim().isEmpty) ? 'Please enter mobile/ID' : null,
                              ),
                              const SizedBox(height: 12),

                              // Password Input with show/hide eye toggle
                              TextFormField(
                                controller: _passwordController,
                                obscureText: _obscurePassword,
                                decoration: InputDecoration(
                                  hintText: 'Password',
                                  prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20, color: Color(0xFF64748B)),
                                  suffixIcon: IconButton(
                                    icon: Icon(
                                      _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                      size: 20,
                                      color: const Color(0xFF64748B),
                                    ),
                                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                                  ),
                                  filled: true,
                                  fillColor: isDark ? const Color(0xFF0F172A) : const Color(0xFFF8FAFC),
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                  enabledBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(16),
                                    borderSide: BorderSide(color: isDark ? const Color(0xFF334155) : const Color(0xFFE2E8F0)),
                                  ),
                                  focusedBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(16),
                                    borderSide: const BorderSide(color: Color(0xFF1E824C), width: 1.8),
                                  ),
                                ),
                                validator: (v) => (v == null || v.trim().isEmpty) ? 'Please enter password' : null,
                              ),
                              const SizedBox(height: 16),

                              // Solid Green Log In Button
                              SizedBox(
                                width: double.infinity,
                                height: 48,
                                child: ElevatedButton(
                                  onPressed: _isLoading ? null : _handleLogIn,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFF1E824C),
                                    foregroundColor: Colors.white,
                                    elevation: 2,
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                                  ),
                                  child: _isLoading
                                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                      : const Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            Text('Log In', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
                                            SizedBox(width: 8),
                                            Icon(Icons.arrow_forward_rounded, size: 18),
                                          ],
                                        ),
                                ),
                              ),

                              // ==========================================
                              // CONDITIONAL SECTION: "OR Login as"
                              // ONLY VISIBLE WHEN "Other Login" IS SELECTED
                              // OTHERWISE COMPLETELY HIDDEN
                              // ==========================================
                              if (_isOtherLogin) ...[
                                const SizedBox(height: 20),
                                
                                // Divider: ─── OR ───
                                Row(
                                  children: [
                                    Expanded(child: Divider(color: Colors.grey.shade300, thickness: 1)),
                                    Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 10),
                                      child: Text(
                                        'OR',
                                        style: TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w800,
                                          color: Colors.grey.shade500,
                                        ),
                                      ),
                                    ),
                                    Expanded(child: Divider(color: Colors.grey.shade300, thickness: 1)),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Login as',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                                const SizedBox(height: 12),

                                // 3 Role Selector Options:
                                // [ Health Worker ] [ Doctor ] [ Health Officer ]
                                Row(
                                  children: [
                                    _buildOtherRoleItem('Health Worker', Icons.medical_services_rounded),
                                    const SizedBox(width: 8),
                                    _buildOtherRoleItem('Doctor', Icons.health_and_safety_rounded),
                                    const SizedBox(width: 8),
                                    _buildOtherRoleItem('Health Officer', Icons.security_rounded),
                                  ],
                                ),

                                const SizedBox(height: 14),
                                // Bottom Leaf Accent: ── 🌿 ──
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Container(width: 24, height: 1, color: Colors.grey.shade300),
                                    const Padding(
                                      padding: EdgeInsets.symmetric(horizontal: 8),
                                      child: Text('🌿', style: TextStyle(fontSize: 14)),
                                    ),
                                    Container(width: 24, height: 1, color: Colors.grey.shade300),
                                  ],
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildOtherRoleItem(String roleName, IconData icon) {
    final isSelected = _selectedOtherRole == roleName;

    return Expanded(
      child: InkWell(
        onTap: () => _onSelectOtherRole(roleName),
        borderRadius: BorderRadius.circular(14),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 2),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFFE8F7F0) : const Color(0xFFF8FAFC),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: isSelected ? const Color(0xFF1E824C) : const Color(0xFFE2E8F0),
              width: isSelected ? 1.8 : 1.0,
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 20,
                color: isSelected ? const Color(0xFF1E824C) : const Color(0xFF64748B),
              ),
              const SizedBox(height: 4),
              Text(
                roleName,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 9.5,
                  fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                  color: isSelected ? const Color(0xFF1E824C) : const Color(0xFF475569),
                  height: 1.15,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
