<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

class BenchmarkAuth extends Command
{
    protected $signature = 'benchmark:auth
                            {--iterations=50 : Jumlah iterasi per skenario}
                            {--warmup=10 : Jumlah iterasi warm-up}';

    protected $description = 'Benchmark Argon2id authentication via Laravel (makro layer)';

    private array $scenarios = [
        ['label' => 'A_Baseline',     'memory' => 10240,  'time' => 2, 'parallelism' => 1],
        ['label' => 'B_OWASP_Min',    'memory' => 19456,  'time' => 2, 'parallelism' => 1],
        ['label' => 'C_OWASP_High',   'memory' => 47104,  'time' => 1, 'parallelism' => 1],
        ['label' => 'D_RFC_SECOND',   'memory' => 65536,  'time' => 3, 'parallelism' => 4],
        ['label' => 'E_High_Security','memory' => 131072, 'time' => 4, 'parallelism' => 1],
        ['label' => 'F_High_Memory',  'memory' => 262144, 'time' => 1, 'parallelism' => 1],
        ['label' => 'G_Parallel_2',   'memory' => 65536,  'time' => 3, 'parallelism' => 2],
        ['label' => 'H_Parallel_1',   'memory' => 65536,  'time' => 3, 'parallelism' => 1],
    ];

    public function handle(): int
    {
        $iterations = (int) $this->option('iterations');
        $warmup = (int) $this->option('warmup');

        $outputDir = storage_path('app/benchmark');
        if (!is_dir($outputDir)) {
            mkdir($outputDir, 0755, true);
        }

        $outputFile = $outputDir . '/results_macro_' . date('Y-m-d_H-i-s') . '.csv';
        $fp = fopen($outputFile, 'w');
        fputcsv($fp, ['scenario', 'memory_cost', 'time_cost', 'parallelism', 'iteration', 'login_time_ms', 'hash_time_ms']);

        $this->info("=== Argon2id Makro Benchmark (Laravel) ===");
        $this->info("Iterations: {$iterations} (+ {$warmup} warm-up)");
        $this->info("Output: {$outputFile}\n");

        $email = 'benchmark@test.com';
        $password = 'benchmark_password_123';

        foreach ($this->scenarios as $scenario) {
            $this->line("Scenario: {$scenario['label']} (m={$scenario['memory']}, t={$scenario['time']}, p={$scenario['parallelism']})...");

            config(['hashing.argon.memory' => $scenario['memory']]);
            config(['hashing.argon.time' => $scenario['time']]);
            config(['hashing.argon.threads' => $scenario['parallelism']]);

            // Rehash the test user password with current scenario parameters
            $user = User::where('email', $email)->first();
            if ($user) {
                $user->password = Hash::make($password);
                $user->save();
            } else {
                $user = User::create([
                    'name' => 'Benchmark User',
                    'email' => $email,
                    'password' => Hash::make($password),
                ]);
            }
            $currentHash = $user->password;

            // Verifikasi parameter hash
            $info = password_get_info($currentHash);
            $actualMemory = $info['options']['memory_cost'] ?? null;
            $actualTime = $info['options']['time_cost'] ?? null;
            $actualThreads = $info['options']['threads'] ?? null;

            if ($actualMemory !== $scenario['memory'] || $actualTime !== $scenario['time'] || $actualThreads !== $scenario['parallelism']) {
                $this->warn("  PARAM MISMATCH (got m={$actualMemory}, t={$actualTime}, p={$actualThreads}) — SKIPPED");
                continue;
            }

            // Warm-up
            for ($w = 0; $w < $warmup; $w++) {
                Auth::attempt(['email' => $email, 'password' => $password]);
                Auth::logout();
            }

            // Pengukuran
            for ($i = 1; $i <= $iterations; $i++) {
                Auth::logout();

                // Full login time (includes DB lookup + hash verify + session)
                $loginStart = hrtime(true);
                $attempt = Auth::attempt(['email' => $email, 'password' => $password]);
                $loginTime = (hrtime(true) - $loginStart) / 1e6;

                if (!$attempt) {
                    $this->error("  Auth::attempt failed on iteration {$i}");
                    continue;
                }

                // Hash-only time (for comparison with micro)
                $hashStart = hrtime(true);
                Hash::check($password, $currentHash);
                $hashTime = (hrtime(true) - $hashStart) / 1e6;

                fputcsv($fp, [
                    $scenario['label'],
                    $scenario['memory'],
                    $scenario['time'],
                    $scenario['parallelism'],
                    $i,
                    round($loginTime, 4),
                    round($hashTime, 4),
                ]);
            }

            $this->info("  DONE");
        }

        fclose($fp);
        $this->newLine();
        $this->info("Results saved to: {$outputFile}");

        return self::SUCCESS;
    }
}
