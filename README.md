# Argon2id Benchmark

Implementasi dan analisis optimasi parameter Argon2id pada sistem autentikasi aplikasi web berbasis Laravel.

**Skripsi** — Rio Mayesta (22SA31A017)
Universitas Amikom Purwokerto, 2026

## Spesifikasi Pengujian

| Komponen | Versi |
|---|---|
| PHP | 8.3.31 (sodium/Argon2id) |
| Laravel | 13.11.2 |
| Database | SQLite |
| OS | Windows 10 64-bit |
| CPU | Intel Core i3-10110U (2C/4T) |
| RAM | 4 GB |

## 8 Skenario Parameter

| Skenario | memory (KiB) | time | parallelism | Sumber |
|---|---|---|---|---|
| A Baseline | 10240 | 2 | 1 | Laravel default |
| B OWASP Min | 19456 | 2 | 1 | OWASP 2024 minimum |
| C OWASP High | 47104 | 1 | 1 | OWASP 2024 high-memory |
| D RFC SECOND | 65536 | 3 | 4 | RFC 9106 SECOND RECOMMENDED |
| E High Security | 131072 | 4 | 1 | Custom |
| F High Memory | 262144 | 1 | 1 | Custom |
| G Parallel 2 | 65536 | 3 | 2 | Isolasi parallelism |
| H Parallel 1 | 65536 | 3 | 1 | Isolasi parallelism |

## Pengukuran Dua Layer

```
LAYER 1: MIKRO (PHP CLI murni)  →  Waktu hashing murni Argon2id
LAYER 2: MAKRO (Laravel HTTP)   →  Waktu verifikasi login
OVERHEAD = Makro - Mikro
```

## Instalasi

```bash
composer install
cp .env.example .env
php artisan key:generate
touch database/database.sqlite
php artisan migrate --seed
```

## Menjalankan Benchmark

```bash
# Layer 1: Mikro (PHP CLI murni)
php benchmark/micro_benchmark.php

# Layer 2: Makro (Laravel)
php artisan benchmark:auth

# Analisis (Python)
python benchmark/analyze_results.py \
  --micro benchmark/results/results_micro_*.csv \
  --macro storage/app/benchmark/results_macro_*.csv
```

## Output Analisis

- `benchmark/results/charts/` — 6 chart PNG (bar, grouped bar, overhead, boxplot)
- `benchmark/results/analysis_combined.csv` — rekapitulasi statistik
- `benchmark/results/anova_results.csv` — hasil ANOVA
- `benchmark/results/tukey_micro.csv` + `tukey_macro.csv` — pairwise comparison

## Dependensi Analisis

```bash
pip install pandas scipy matplotlib seaborn
```

## Referensi

1. Biryukov et al. (2021). RFC 9106 — Argon2 Memory-Hard Function.
2. OWASP (2024). Password Storage Cheat Sheet.
3. Eum et al. (2023). Optimized Implementation of Argon2 Utilizing GPU.
4. Listiawan et al. (2024). Optimising Bcrypt Parameters.
5. Fedorchenko et al. (2024). Password Hashing Methods on .NET Platform.

## License

MIT
