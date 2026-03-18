import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import '../services/api_service.dart';

class ReportScreen extends StatefulWidget {
  final LatLng userLocation;
  const ReportScreen({super.key, required this.userLocation});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  final _titleController = TextEditingController();
  final _descController  = TextEditingController();

  List<dynamic> _categories = [];
  int? _selectedCategoryId;
  String _severity = 'low';
  bool _loading = false;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    setState(() => _loading = true);
    final cats = await ApiService.getCategories();
    setState(() {
      _categories = cats;
      if (cats.isNotEmpty) _selectedCategoryId = cats[0]['id'];
      _loading = false;
    });
  }

  Future<void> _submit() async {
    if (_titleController.text.isEmpty || _selectedCategoryId == null) return;

    setState(() => _submitting = true);

    final success = await ApiService.submitReport(
      categoryId: _selectedCategoryId!,
      title: _titleController.text.trim(),
      description: _descController.text.trim().isEmpty ? null : _descController.text.trim(),
      latitude: widget.userLocation.latitude,
      longitude: widget.userLocation.longitude,
      severity: _severity,
    );

    setState(() => _submitting = false);

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Report submitted. Thanks for keeping people safe.')),
      );
      Navigator.pop(context);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Something went wrong. Please try again.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report an incident')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(20),
              child: ListView(
                children: [
                  const Text('What happened?', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),

                  // Category selector
                  DropdownButtonFormField<int>(
                    value: _selectedCategoryId,
                    decoration: const InputDecoration(
                      labelText: 'Incident type',
                      border: OutlineInputBorder(),
                    ),
                    items: _categories.map<DropdownMenuItem<int>>((cat) {
                      return DropdownMenuItem<int>(
                        value: cat['id'] as int,
                        child: Text('${cat['icon']}  ${cat['name']}'),
                      );
                    }).toList(),
                    onChanged: (v) => setState(() => _selectedCategoryId = v),
                  ),
                  const SizedBox(height: 16),

                  // Title
                  TextField(
                    controller: _titleController,
                    decoration: const InputDecoration(
                      labelText: 'Short description',
                      hintText: 'e.g. Smash and grab on De Waal Drive',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Details (optional)
                  TextField(
                    controller: _descController,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'More details (optional)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Severity
                  const Text('How serious is it?'),
                  const SizedBox(height: 8),
                  SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(value: 'low',    label: Text('Minor')),
                      ButtonSegment(value: 'medium', label: Text('Serious')),
                      ButtonSegment(value: 'high',   label: Text('Dangerous')),
                    ],
                    selected: {_severity},
                    onSelectionChanged: (s) => setState(() => _severity = s.first),
                  ),
                  const SizedBox(height: 24),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _submitting ? null : _submit,
                      icon: _submitting
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.send),
                      label: const Text('Submit report'),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
