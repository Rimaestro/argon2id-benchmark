<?php

/**
 * Mikro Benchmark: Mengukur waktu hashing dan verifikasi Argon2id secara murni (PHP CLI).
 * Tanpa framework overhead — murni password_hash() dan password_verify().
 *
 * Output: CSV dengan kolom scenario, memory_cost, time_cost, parallelism, iteration,
 *         hashing_time_ms, verify_time_ms
 */

$scenarios = [
    ['label' => 'A_Baseline',     'memory' => 10240,  'time' => 2, 'parallelism' => 1],
    ['label' => 'B_OWASP_Min',    'memory' => 19456,  'time' => 2, 'parallelism' => 1],
    ['label' => 'C_OWASP_High',   'memory' => 47104,  'time' => 1, 'parallelism' => 1],
    ['label' => 'D_RFC_SECOND',   'memory' => 65536,  'time' => 3, 'parallelism' => 4],
    ['label' => 'E_High_Security','memory' => 131072, 'time' => 4, 'parallelism' => 1],
    ['label' => 'F_High_Memory',  'memory' => 262144, 'time' => 1, 'parallelism' => 1],
    ['label' => 'G_Parallel_2',   'memory' => 65536,  'time' => 3, 'parallelism' => 2],
    ['label' => 'H_Parallel_1',   'memory' => 65536,  'time' => 3, 'parallelism' => 1],
];

$iterations = 50;
$warmup = 10;
$password = 'benchmark_password_123';

$outputDir = __DIR__ . '/results';
if (!is_dir($outputDir)) {
    mkdir($outputDir, 0755, true);
}

$outputFile = $outputDir . '/results_micro_' . date('Y-m-d_H-i-s') . '.csv';
$fp = fopen($outputFile, 'w');
fputcsv($fp, ['scenario', 'memory_cost', 'time_cost', 'parallelism', 'iteration', 'hashing_time_ms', 'verify_time_ms']);

echo "=== Argon2id Mikro Benchmark ===\n";
echo "Iterations: {$iterations} (+ {$warmup} warm-up)\n";
echo "Password: '{$password}'\n";
echo "Output: {$outputFile}\n\n";

foreach ($scenarios as $scenario) {
    echo "Scenario: {$scenario['label']} (m={$scenario['memory']}, t={$scenario['time']}, p={$scenario['parallelism']})... ";

    $options = [
        'memory_cost' => $scenario['memory'],
        'time_cost' => $scenario['time'],
        'threads' => $scenario['parallelism'],
    ];

    // Warm-up
    for ($w = 0; $w < $warmup; $w++) {
        password_hash($password, PASSWORD_ARGON2ID, $options);
    }

    // Pengukuran
    for ($i = 1; $i <= $iterations; $i++) {
        $start = hrtime(true);
        $hash = password_hash($password, PASSWORD_ARGON2ID, $options);
        $hashTime = (hrtime(true) - $start) / 1e6;

        $start = hrtime(true);
        password_verify($password, $hash);
        $verifyTime = (hrtime(true) - $start) / 1e6;

        fputcsv($fp, [
            $scenario['label'],
            $scenario['memory'],
            $scenario['time'],
            $scenario['parallelism'],
            $i,
            round($hashTime, 4),
            round($verifyTime, 4),
        ]);
    }

    echo "DONE\n";
}

fclose($fp);
echo "\nResults saved to: {$outputFile}\n";
