<?php
// start.php
// Tries to start the Flask app (app.py) in background on Windows.
// WARNING: This uses `start` and will spawn a background process. Make sure PHP has permission to run processes.

header('Content-Type: application/json');

$script = realpath(__DIR__ . DIRECTORY_SEPARATOR . 'app.py');
if (!$script) {
    echo json_encode(['error' => 'Tidak dapat menemukan app.py di direktori proyek.']);
    exit;
}

$python = 'python'; // asumsikan python ada di PATH; ubah jika perlu ke path lengkap

// On Windows, use start to run in background. Provide an empty title string "" after start.
$cmd = 'start /B "" ' . escapeshellarg($python) . ' ' . escapeshellarg($script);

// Execute the command
exec($cmd . ' 2>&1', $output, $returnVar);

echo json_encode(['cmd' => $cmd, 'output' => $output, 'return' => $returnVar]);
?>
