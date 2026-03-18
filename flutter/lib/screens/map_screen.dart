import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../services/api_service.dart';
import 'report_screen.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final MapController _mapController = MapController();

  LatLng _currentLocation = const LatLng(-33.9249, 18.4241); // Default: Cape Town
  List<dynamic> _reports = [];
  bool _loadingLocation = true;

  @override
  void initState() {
    super.initState();
    _getLocationAndLoadReports();
  }

  Future<void> _getLocationAndLoadReports() async {
    try {
      // Ask for location permission
      LocationPermission permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        setState(() => _loadingLocation = false);
        return;
      }

      final position = await Geolocator.getCurrentPosition();
      setState(() {
        _currentLocation = LatLng(position.latitude, position.longitude);
        _loadingLocation = false;
      });

      // Load reports around the user
      await _loadReports();
    } catch (e) {
      setState(() => _loadingLocation = false);
    }
  }

  Future<void> _loadReports() async {
    final reports = await ApiService.getMapReports(
      lat: _currentLocation.latitude,
      lng: _currentLocation.longitude,
    );
    setState(() => _reports = reports);
  }

  List<Marker> _buildMarkers() {
    final markers = <Marker>[];

    // User location marker
    markers.add(
      Marker(
        point: _currentLocation,
        width: 40,
        height: 40,
        child: const Icon(Icons.my_location, color: Colors.blue, size: 32),
      ),
    );

    // Incident markers
    for (final report in _reports) {
      final lat = report['latitude'] as double;
      final lng = report['longitude'] as double;
      final icon = report['category_icon'] ?? '⚠️';
      final title = report['title'] ?? '';

      markers.add(
        Marker(
          point: LatLng(lat, lng),
          width: 48,
          height: 48,
          child: GestureDetector(
            onTap: () => _showReportDetail(report),
            child: Container(
              decoration: BoxDecoration(
                color: _severityColor(report['severity']),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2),
              ),
              child: Center(
                child: Text(icon, style: const TextStyle(fontSize: 20)),
              ),
            ),
          ),
        ),
      );
    }

    return markers;
  }

  Color _severityColor(String? severity) {
    switch (severity) {
      case 'high':   return Colors.red.withOpacity(0.85);
      case 'medium': return Colors.orange.withOpacity(0.85);
      default:       return Colors.yellow.withOpacity(0.85);
    }
  }

  void _showReportDetail(Map report) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${report['category_icon']}  ${report['title']}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            if (report['description'] != null)
              Text(report['description']),
            const SizedBox(height: 8),
            Text('${report['vote_count']} people reported this',
                style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () async {
                await ApiService.voteOnReport(report['id']);
                Navigator.pop(ctx);
                await _loadReports();
              },
              child: const Text('I can confirm this'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Witness', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadReports,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: _loadingLocation
          ? const Center(child: CircularProgressIndicator())
          : FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: _currentLocation,
                initialZoom: 14.0,
                minZoom: 5.0,
                maxZoom: 18.0,
              ),
              children: [
                // OpenStreetMap tile layer — completely free
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.witness.app',
                ),
                MarkerLayer(markers: _buildMarkers()),
              ],
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ReportScreen(userLocation: _currentLocation),
            ),
          );
          await _loadReports(); // Refresh map after submitting
        },
        icon: const Icon(Icons.add_alert),
        label: const Text('Report'),
      ),
    );
  }
}
