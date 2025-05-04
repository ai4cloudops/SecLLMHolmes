import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from statistics import mode

BENCHMARK_PATH = os.path.join(os.path.dirname(__file__), '..', 'results', 'benchmark')

def load_benchmark(model: str):
    benchmark_file = os.path.join(BENCHMARK_PATH, f'{model}.json')
    if not os.path.exists(benchmark_file):
        raise FileNotFoundError(f"Benchmark file for model '{model}' not found.")
    with open(benchmark_file, 'r') as f:
        benchmark_data = json.load(f)
    return benchmark_data

def handle_reason(r, c, g):
    if r and c:
        return 1 if g == 'yes' else 0
        ROUGE_THRES = 0.34
        COS_SIM_THRES = 0.84
        return mode([1 if r >= ROUGE_THRES else 0, 1 if c >= COS_SIM_THRES else 0, 1 if g=='yes' else 0])
    return 0

def evaluate_hand_crafted(data: dict):
    correct, total = 0, 0
    for cwe in data['hand-crafted']:
        for file in data['hand-crafted'][cwe]:
            total += 1
            y_true = "yes" if data['hand-crafted'][cwe][file]['label'] else "no"
            y_pred = data['hand-crafted'][cwe][file]['pred']
            r_pred = handle_reason(
                data['hand-crafted'][cwe][file]['rouge'],
                data['hand-crafted'][cwe][file]['cos_sim'],
                data['hand-crafted'][cwe][file]['gpt_eval']
            )
            if y_true == y_pred and r_pred:
                correct += 1
    return {"correct": correct, "total": total}

def evaluate_trivial(data: dict):
    correct, total = 0, 0
    for scenario in data['augmented']['trivial']:
        for cwe in data['augmented']['trivial'][scenario]:
            for file in data['augmented']['trivial'][scenario][cwe]:
                total += 1

                # after augmentation version
                y_pred = data['augmented']['trivial'][scenario][cwe][file]['pred']
                r_pred = handle_reason(
                    data['augmented']['trivial'][scenario][cwe][file]['rouge'],
                    data['augmented']['trivial'][scenario][cwe][file]['cos_sim'],
                    data['augmented']['trivial'][scenario][cwe][file]['gpt_eval']
                )

                # before augmentation version
                y_pred_b = data['hand-crafted'][cwe][file]['pred']
                r_pred_b = handle_reason(
                    data['hand-crafted'][cwe][file]['rouge'],
                    data['hand-crafted'][cwe][file]['cos_sim'],
                    data['hand-crafted'][cwe][file]['gpt_eval']
                )

                # check if both predictions are same
                if y_pred == y_pred_b and r_pred == r_pred_b:
                    correct += 1
    return {"correct": correct, "total": total}

def evaluate_non_trivial(data: dict):
    correct, total = 0, 0
    for scenario in data['augmented']['non-trivial']:
        for cwe in data['augmented']['non-trivial'][scenario]['0']:
            for file in data['augmented']['non-trivial'][scenario]['0'][cwe]:
                total += 1

                # before augmentation version
                y_pred = data['augmented']['non-trivial'][scenario]['0'][cwe][file]['pred']
                r_pred = handle_reason(
                    data['augmented']['non-trivial'][scenario]['0'][cwe][file]['rouge'],
                    data['augmented']['non-trivial'][scenario]['0'][cwe][file]['cos_sim'],
                    data['augmented']['non-trivial'][scenario]['0'][cwe][file]['gpt_eval']
                )

                # after augmentation version
                y_pred_b = data['augmented']['non-trivial'][scenario]['1'][cwe][file]['pred']
                r_pred_b = handle_reason(
                    data['augmented']['non-trivial'][scenario]['1'][cwe][file]['rouge'],
                    data['augmented']['non-trivial'][scenario]['1'][cwe][file]['cos_sim'],
                    data['augmented']['non-trivial'][scenario]['1'][cwe][file]['gpt_eval']
                )

                # check if both predictions are same
                if y_pred == y_pred_b and r_pred == r_pred_b:
                    correct += 1
    return {"correct": correct, "total": total}

def evaluate_real_world(data: dict):
    correct, total = 0, 0
    for project in data['real-world']:
        for cve in data['real-world'][project]:
            for scenario in data['real-world'][project][cve]:
                total += 1
                y_true = "yes" if scenario=='vuln' else "no"
                y_pred = data['real-world'][project][cve][scenario]['pred']
                r_pred = handle_reason(
                    data['real-world'][project][cve][scenario]['rouge'],
                    data['real-world'][project][cve][scenario]['cos_sim'],
                    data['real-world'][project][cve][scenario]['gpt_eval']
                )
                final_pred = (y_true == y_pred) and r_pred
                if final_pred:
                    correct += 1
    return {"correct": correct, "total": total}

def benchmark():
    results = {}
    for file in os.listdir(BENCHMARK_PATH):
        if file.endswith('.json'):
            model = file[:-5]
            if model not in results:
                results[model] = {}
            benchmark_data = load_benchmark(model)
            results[model]['hand-crafted'] = evaluate_hand_crafted(benchmark_data)
            results[model]['trivial'] = evaluate_trivial(benchmark_data)
            results[model]['non-trivial'] = evaluate_non_trivial(benchmark_data)
            results[model]['real-world'] = evaluate_real_world(benchmark_data)
    return results

def console_benchmark():
    results = benchmark()
    for model, data in results.items():
        print(f"Model: {model}")
        for category, result in data.items():
            correct = result['correct']
            total = result['total']
            accuracy = (correct / total) * 100 if total > 0 else 0
            print(f"  {category}: {correct}/{total} ({accuracy:.2f}%)")
    print("\n")

def plot_benchmark():
    results = benchmark()
    model_labels = {
        'o3': 'o3',
        'o1': 'o1',
        'o4-mini': 'o4-mini',
        'gpt-3.5-turbo': 'GPT-3.5',
        'gpt-4': 'GPT-4',
        'gpt-4-turbo': 'GPT-4-Turbo',
        'gpt-4.1': 'GPT-4.1',
        'gpt-4o-2024-11-20': 'GPT-4o',
        'claude-3-5-sonnet-20241022': 'Claude-3.5-Sonnet',
        'claude-3-7-sonnet-20250219': 'Claude-3.7-Sonnet',
        'Llama-4-Maverick-17B-128E-Instruct-FP8': 'Llama-4-Maverick',
        'DeepSeek-R1': 'DeepSeek-R1'
    }
    synthetic_x = []
    real_y = []
    trivial_x = []
    nontrivial_y = []
    labels = []

    for model, cats in results.items():
        hc = cats['hand-crafted']
        triv = cats['trivial']
        non_triv = cats['non-trivial']
        real = cats['real-world']
        
        # Compute accuracies as percentages
        triv_acc = triv['correct'] / triv['total'] * 100
        non_triv_acc = non_triv['correct'] / non_triv['total'] * 100
        hc_acc = hc['correct'] / hc['total'] * 100
        real_acc = real['correct'] / real['total'] * 100
        
        synthetic_correct = hc['correct'] + triv['correct'] + non_triv['correct']
        synthetic_total = hc['total'] + triv['total'] + non_triv['total']
        synthetic_acc = synthetic_correct / synthetic_total * 100
        
        synthetic_x.append(synthetic_acc)
        real_y.append(real_acc)
        trivial_x.append(triv_acc)
        nontrivial_y.append(non_triv_acc)
        labels.append(model_labels[model])

    # Figure 1: Synthetic vs Real-world accuracy
    plt.figure()
    plt.scatter(synthetic_x, real_y)
    for i, label in enumerate(labels):
        plt.text(synthetic_x[i] + 0.2, real_y[i] + 0.2, label, fontsize=8)
    plt.xlabel('Synthetic (%)')
    plt.ylabel('Real‑world (%)')
    plt.title('Synthetic vs Real‑world Accuracy')

    # Figure 2: Trivial vs Non‑trivial accuracy
    plt.figure()
    plt.scatter(trivial_x, nontrivial_y)
    for i, label in enumerate(labels):
        plt.text(trivial_x[i] + 0.2, nontrivial_y[i] + 0.2, label, fontsize=8)
    plt.xlabel('Trivial accuracy (%)')
    plt.ylabel('Non‑trivial accuracy (%)')
    plt.title('Trivial vs Non‑trivial Test Passed')

    plt.show()
    
if __name__ == "__main__":
    console_benchmark()
    plot_benchmark()
