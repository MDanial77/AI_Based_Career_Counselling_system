"""Regenerate the training dataset and compare the four ML models.

Usage:  python train_model.py
Output: Database/ml/training_dataset.csv and Database/ml/model_metrics.json
"""
from Database.ml_model import train_and_save_metrics

if __name__ == "__main__":
    print("Generating dataset and running 10-fold cross-validation...")
    metrics = train_and_save_metrics()
    print(f"Dataset: {metrics['dataset_size']} profiles, "
          f"{metrics['classes']} careers, {metrics['features']} features\n")
    print(f"{'Model':<24}{'Accuracy':>10}{'Precision':>11}{'Recall':>9}{'F1':>8}")
    for r in metrics["results"]:
        print(f"{r['model']:<24}{r['accuracy']:>9}%{r['precision']:>11}"
              f"{r['recall']:>9}{r['f1']:>8}")
