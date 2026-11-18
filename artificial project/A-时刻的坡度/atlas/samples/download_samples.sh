#!/usr/bin/env bash
# 短小重下载脚本（不是分析框架）。用于从原地址再取今晚用过的文件。
# 采集环境记录见 ../来源与许可证/采集记录.md
set -euo pipefail
DEST="${1:-.}"
mkdir -p "$DEST"
cd "$DEST"

echo "1) Official MTA subway Regular GTFS"
curl -L --fail -o gtfs_subway.zip \
  "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"

echo "2) transitlab monthly parquet (third-party snapshot of official hourly ridership), August 2026"
curl -L --fail -o subway_hourly_ridership_2026-08.parquet \
  "https://data.transitlab.nyc/v1/subway_hourly_ridership/year=2026/month=08/2026-08.parquet"

echo "3) Official MTA Subway Stations mapping (data.ny.gov). This host returned HTTP 403 from some datacenter IPs."
set +e
curl -L --fail -o mta_subway_stations.csv \
  "https://data.ny.gov/resource/39hk-dx4f.csv?\$limit=500&\$order=station_id"
status=$?
set -e
if [ "$status" -ne 0 ]; then
  echo "WARN: data.ny.gov download failed (exit $status). Try another network, or open the URL in a browser." >&2
fi

echo "4) Open-Meteo Lanzhou air quality, 2026-08-03 to 2026-08-09 (CC BY 4.0; city reference point, not a surveyed campus coordinate)"
curl -L --fail -o openmeteo_lanzhou_air_quality_2026-08-03_to_2026-08-09.csv \
  "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=36.06&longitude=103.83&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,uv_index,european_aqi&start_date=2026-08-03&end_date=2026-08-09&timezone=Asia%2FShanghai&format=csv"

echo "5) Open-Meteo Lanzhou historical weather, same week (CC BY 4.0)"
curl -L --fail -o openmeteo_lanzhou_weather_2026-08-03_to_2026-08-09.csv \
  "https://archive-api.open-meteo.com/v1/archive?latitude=36.06&longitude=103.83&start_date=2026-08-03&end_date=2026-08-09&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,surface_pressure&timezone=Asia%2FShanghai&format=csv"

echo "Note: STM32 CSV/JSONL/USART files in this directory are simulated (模拟，非实机) and are not downloaded by this script."

echo "Done in $DEST"
ls -la gtfs_subway.zip subway_hourly_ridership_2026-08.parquet mta_subway_stations.csv \
  openmeteo_lanzhou_air_quality_2026-08-03_to_2026-08-09.csv \
  openmeteo_lanzhou_weather_2026-08-03_to_2026-08-09.csv 2>/dev/null || true
