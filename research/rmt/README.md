# Практическая часть Assignment 3

Это выполненный первый эксперимент по прогнозу результативности футболистов после трансфера. Данные реальные; результаты находятся в outputs. Отчёт на английском соответствует языку Assignments 1 и 2.

## Как повторить запуск

Нужен Python 3.12. Из папки practical:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run_pipeline.py
```


## Файлы

- run_pipeline.py — весь выполняемый код, включая проверки хронологии, построение выборки, модели, метрики и анализ ошибок.
- data — четыре исходных сжатых CSV, загруженные 12 октября 2026 года из открытого проекта dcaribou/transfermarkt-datasets.
- outputs/source_manifest.json — URL источников, дата получения и SHA-256 каждого исходного файла.
- outputs/transfer_cohort.csv — 781 трансфер с признаками, целевым значением и временным разбиением.
- outputs/results.json — полные результаты и настройки.
- outputs/test_predictions.csv — фактические значения, прогнозы обеих моделей и ошибки для 242 тестовых трансферов.
- outputs/permutation_importance.csv — важность признаков на тестовой выборке.
- outputs/largest_errors.csv — примеры максимальных ошибок.
- outputs/formation_rf.joblib — обученная модель с препроцессингом.
- outputs/run_log.txt — журнал фактического запуска.



```powershell
.venv\Scripts\python.exe demonstrate_transfer.py --player-id 132098
```

